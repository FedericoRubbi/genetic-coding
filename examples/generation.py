# pip install "hypothesis[lark]"
from lark import Lark
from hypothesis import strategies as st
from hypothesis.extra.lark import from_lark

# --- Parsers ---
# Your real parser (Earley+dynamic) for validation
earley = Lark.open("data/main.lark", start="control_pattern")  # default earley/dynamic

# A generation-only parser to avoid dynamic-lexer edge cases
gen = Lark.open("data/main.lark", start="control_pattern", parser="lalr", lexer="contextual")

# --- Helper: auto-map base terminal names -> mangled names present in the compiled grammar
def make_explicit(gen_lark, base_to_strategy):
    term_names = {t.name for t in gen_lark.terminals}  # all TerminalDefs, mangled
    explicit = {}
    for base, strat in base_to_strategy.items():
        # Add exact match and any name that ends with "__" + base
        matches = [n for n in term_names if n == base or n.endswith("__" + base)]
        if not matches:
            # Optional: print to see what exists; helps you tweak the bases
            # print(f"[warn] No terminal for {base}")
            continue
        for m in matches:
            explicit[m] = strat
    return explicit

# --- Your preferred distributions for domain tokens & numbers (unmangled base names) ---
base_explicit = {
    # finite string domains
    "SAMPLE_STRING": st.sampled_from(['"bd"', '"sn"', '"hh"', '"tabla"']),
    "VOWEL_STRING":  st.sampled_from(['"a"', '"e"', '"i"', '"o"', '"u"']),
    "SCALE_STRING":  st.sampled_from(['"minor"', '"major"', '"dorian"']),
    "PARAM_STRING":  st.sampled_from(['"pan"', '"gain"', '"shape"', '"cutoff"']),
    "BUS_STRING":    st.sampled_from(['"gain"', '"speed"', '"pan"']),
    # keep numbers small/readable
    "INT":    st.integers(min_value=0, max_value=12).map(str),
    "DOUBLE": st.floats(min_value=0, max_value=8, allow_nan=False, allow_infinity=False)
                 .map(lambda x: f"{x:.2f}"),
}

base_explicit["SILENCE"] = st.nothing()

# >>> print(getattr(gen, "ignore_tokens", ()))
# ['WS', 'COMMENT', 'BLOCK_COMMENT']

for name in getattr(gen, "ignore_tokens", ()):
    if name == "WS":
        base_explicit[name] = st.just(" ")
    else:
        base_explicit[name] = st.just("")

base_explicit.update({
    # "COMMENT": st.just(""),
    # "LINE_COMMENT": st.just(""),
    # "BLOCK_COMMENT": st.just(""),
    "WS": st.just(" "), # whitespace
})

breakpoint()

explicit = make_explicit(gen, base_explicit)

# Optional: see what terminals exist (so you can confirm mangled names)
# print(sorted(n for n in {t.name for t in gen.grammar.terminals}
#              if any(k in n for k in ["SAMPLE_STRING","VOWEL_STRING","SCALE_STRING","PARAM_STRING","BUS_STRING","INT","DOUBLE"])))

# Keep the alphabet readable and also EXCLUDE '/' and '*' so ignored C-style comments won't appear
alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-'\""
alphabet = st.sampled_from(list(alphabet))

# Strategy of strings that the LALR+contextual parser accepts
cp_strings = from_lark(gen, start="control_pattern", explicit=explicit, alphabet=alphabet)

# --- Validation & cleanup filters ---
def parses_ok(s: str) -> bool:
    try:
        earley.parse(s)  # validate with real parser
        return True
    except Exception:
        return False

# Disallow empty cp_list like "randcat []"
def no_empty_cp_list(s: str) -> bool:
    t = earley.parse(s)
    for st in t.iter_subtrees_topdown():
        if st.data == "cp_list" and len(st.children) == 0:
            return False
    return True

cp_strings = (
    cp_strings
    .filter(lambda s: s.strip())
    .filter(lambda s: len(s) <= 120)
    .filter(parses_ok)
    .filter(no_empty_cp_list)
)

# Trees if you want them
cp_trees = cp_strings.map(earley.parse)

# --- Try one example (fine for exploration) ---
example = cp_strings.example()
print(example)
print(earley.parse(example).pretty())