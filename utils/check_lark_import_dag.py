#!/usr/bin/env python3
import argparse, collections, pathlib, re, sys
from typing import Dict, List, Set, Tuple, Optional

ImportEdge = Tuple[pathlib.Path, pathlib.Path]

IMPORT_RE = re.compile(
    r'^\s*%import\s+([.\w]+)\s*(?:\(|->|\s*$)',
    flags=re.IGNORECASE
)

SINGLE_IMPORT_RE = re.compile(
    r'^\s*%import\s+([.\w]+)\s*([A-Za-z_]\w*)?\s*(?:->\s*([A-Za-z_]\w*))?\s*$',
    flags=re.IGNORECASE
)

RENAME_IN_GROUP_RE = re.compile(
    r'%import\s+[.\w]+\s*\((.*?)\)', flags=re.IGNORECASE
)

RENAME_SINGLE_RE = re.compile(
    r'%import\s+[.\w]+\s*([A-Za-z_]\w*)\s*->\s*([A-Za-z_]\w*)', flags=re.IGNORECASE
)

def strip_line_comment(line: str) -> str:
    # crude but effective for Lark .lark files that use // comments
    i = line.find('//')
    return line if i == -1 else line[:i]

def count_leading_dots(s: str) -> int:
    n = 0
    for ch in s:
        if ch == '.':
            n += 1
        else:
            break
    return n

def resolve_module_to_file(
    current_file: pathlib.Path,
    module: str,
    root: pathlib.Path
) -> Optional[pathlib.Path]:
    """
    Resolve a %import module path to a .lark file path.
    Handles:
      - .pkg
      - ..pkg.sub
      - pkg.sub
      - pkg.sub.RuleName (strip last segment if needed)
    Strategy: try exact path, then try stripping last segment.
    """
    module = module.strip()
    dots = count_leading_dots(module)
    mod = module[dots:]
    segs = [s for s in mod.split('.') if s]

    # Choose base dir for resolution
    if dots == 0:
        base = root  # absolute-like (search under root)
    else:
        base = current_file.parent
        # go up (dots - 1) levels: . => current dir, .. => parent, etc.
        for _ in range(max(0, dots - 1)):
            base = base.parent

    candidates = []
    if segs:
        candidates.append(base.joinpath(*segs).with_suffix('.lark'))
        if len(segs) > 1:
            candidates.append(base.joinpath(*segs[:-1]).with_suffix('.lark'))
    else:
        # Weird case: module is just dots — ignore
        return None

    for c in candidates:
        if c.exists():
            return c

    return None

def collect_imports_for_file(
    file_path: pathlib.Path,
    root: pathlib.Path
) -> Tuple[Set[pathlib.Path], List[Tuple[str, str]]]:
    """Return (set of imported files, list of (module, line))"""
    imports: Set[pathlib.Path] = set()
    unresolved: List[Tuple[str, str]] = []
    text = file_path.read_text(encoding='utf-8', errors='ignore').splitlines()

    for i, raw in enumerate(text, 1):
        line = strip_line_comment(raw).strip()
        if not line.startswith('%import'):
            continue

        m = IMPORT_RE.match(line)
        if not m:
            # Try single-import form like: %import .pkg.rule -> alias
            m2 = SINGLE_IMPORT_RE.match(line)
            if m2:
                module = m2.group(1)  # includes .pkg.rule or .pkg
            else:
                # couldn't parse; record as unresolved
                unresolved.append((f"(unparsed import) {line}", f"{file_path}:{i}"))
                continue
        else:
            module = m.group(1)

        target = resolve_module_to_file(file_path, module, root)
        if target is None:
            unresolved.append((module, f"{file_path}:{i}"))
        else:
            imports.add(target)

    return imports, unresolved

def build_import_graph(
    root: pathlib.Path,
    entry: Optional[pathlib.Path]
) -> Tuple[Dict[pathlib.Path, Set[pathlib.Path]], List[Tuple[str, str]]]:
    """
    If entry provided: BFS from entry to collect reachable files.
    Else: scan all .lark files under root.
    Returns (graph, unresolved_imports)
    """
    graph: Dict[pathlib.Path, Set[pathlib.Path]] = collections.defaultdict(set)
    unresolved: List[Tuple[str, str]] = []

    def process_file(p: pathlib.Path):
        if p in seen:
            return
        seen.add(p)
        imported, unr = collect_imports_for_file(p, root)
        unresolved.extend(unr)
        graph[p].update(imported)
        for q in imported:
            process_file(q)

    seen: Set[pathlib.Path] = set()
    if entry:
        entry = entry.resolve()
        process_file(entry)
    else:
        for p in root.rglob('*.lark'):
            process_file(p.resolve())

    return graph, unresolved

def find_cycles(graph: Dict[pathlib.Path, Set[pathlib.Path]]):
    WHITE, GRAY, BLACK = 0, 1, 2
    color: Dict[pathlib.Path, int] = {u: WHITE for u in graph}
    parent: Dict[pathlib.Path, Optional[pathlib.Path]] = {u: None for u in graph}
    cycles: List[List[pathlib.Path]] = []

    def dfs(u: pathlib.Path):
        color[u] = GRAY
        for v in graph.get(u, ()):
            if v not in color:
                color[v] = WHITE
                parent[v] = u
            if color[v] == WHITE:
                parent[v] = u
                dfs(v)
            elif color[v] == GRAY:
                # found a back-edge u -> v, reconstruct cycle
                cyc = [v]
                x = u
                while x != v and x is not None:
                    cyc.append(x)
                    x = parent.get(x)
                cyc.append(v)
                cyc.reverse()
                # Deduplicate similar cycles
                if cyc not in cycles:
                    cycles.append(cyc)
        color[u] = BLACK

    for u in list(graph.keys()):
        if color[u] == WHITE:
            dfs(u)
    return cycles

def collect_renames(root: pathlib.Path) -> List[Tuple[pathlib.Path, int, str, str]]:
    """Return list of (file, line, from, to) for rename edges NAME -> ALIAS."""
    renames = []
    for p in root.rglob('*.lark'):
        lines = p.read_text(encoding='utf-8', errors='ignore').splitlines()
        for i, raw in enumerate(lines, 1):
            line = strip_line_comment(raw)
            # group form: %import .pkg (A -> B, C, D -> E)
            m = RENAME_IN_GROUP_RE.search(line)
            if m:
                for part in m.group(1).split(','):
                    part = part.strip()
                    m2 = re.match(r'([A-Za-z_]\w*)\s*->\s*([A-Za-z_]\w*)', part)
                    if m2:
                        renames.append((p, i, m2.group(1), m2.group(2)))
            # single form: %import .pkg.name -> alias
            for m3 in RENAME_SINGLE_RE.finditer(line):
                renames.append((p, i, m3.group(1), m3.group(2)))
    return renames

def find_rename_cycles(renames: List[Tuple[pathlib.Path, int, str, str]]):
    g = collections.defaultdict(list)
    for _, _, a, b in renames:
        g[a].append(b)

    seen, stack = set(), []
    cycles = []

    def dfs(u: str):
        stack.append(u)
        seen.add(u)
        for v in g.get(u, []):
            if v in stack:
                j = stack.index(v)
                cycles.append(stack[j:] + [v])
            elif v not in seen:
                dfs(v)
        stack.pop()

    for a, _, _from, _to in renames:
        pass
    for u in list(g.keys()):
        if u not in seen:
            dfs(u)
    return cycles

def write_dot(graph: Dict[pathlib.Path, Set[pathlib.Path]], out_path: pathlib.Path):
    with out_path.open('w', encoding='utf-8') as f:
        f.write('digraph LarkImports {\n')
        for u, vs in graph.items():
            uid = u.as_posix().replace('/', '_').replace('.', '_')
            f.write(f'  "{u}" [shape=box];\n')
            for v in vs:
                vid = v.as_posix().replace('/', '_').replace('.', '_')
                f.write(f'  "{u}" -> "{v}";\n')
        f.write('}\n')

def main():
    ap = argparse.ArgumentParser(description="Check Lark import DAG and rename cycles")
    ap.add_argument(
        '--root',
        default='src/genetic_music/grammar',
        help='Root folder for grammar files',
    )
    ap.add_argument('--entry', default=None, help='Entry grammar file (optional)')
    ap.add_argument('--dot', default=None, help='Write Graphviz .dot to this path')
    args = ap.parse_args()

    root = pathlib.Path(args.root).resolve()
    if args.entry:
        entry = pathlib.Path(args.entry).resolve()
        if not entry.exists():
            print(f"[ERROR] Entry file not found: {entry}", file=sys.stderr)
            sys.exit(1)
    else:
        entry = None

    graph, unresolved = build_import_graph(root, entry)

    # Print summary
    all_files = sorted(graph.keys())
    edge_count = sum(len(v) for v in graph.values())
    print(f"Files: {len(all_files)}, Edges: {edge_count}")

    if unresolved:
        print("\nUnresolved imports:")
        for mod, loc in unresolved:
            print(f"  {loc}: {mod}")

    # Cycles
    cycles = find_cycles(graph)
    if cycles:
        print("\nIMPORT CYCLES FOUND:")
        for cyc in cycles:
            print("  - " + "  ->  ".join(str(p) for p in cyc))
    else:
        print("\nNo import cycles.")

    # Rename cycles
    ren = collect_renames(root)
    if ren:
        print(f"\nRenames found: {len(ren)}")
        rcyc = find_rename_cycles(ren)
        if rcyc:
            print("RENAME CYCLES FOUND:")
            for cyc in rcyc:
                print("  - " + " -> ".join(cyc))
        else:
            print("No rename cycles.")
    else:
        print("\nRenames: []\nNo rename cycles.")

    # Dot
    if args.dot:
        out = pathlib.Path(args.dot).resolve()
        write_dot(graph, out)
        print(f"\nDOT written to: {out}")

if __name__ == '__main__':
    main()