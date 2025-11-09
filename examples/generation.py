# pip install "hypothesis[lark]"
from lark import Lark, Token
from hypothesis import strategies as st
from hypothesis.extra.lark import from_lark

import warnings
from hypothesis.errors import HypothesisWarning, NonInteractiveExampleWarning
warnings.filterwarnings("ignore", category=NonInteractiveExampleWarning)
warnings.filterwarnings("ignore", category=HypothesisWarning)

def needs_space(prev: Token, cur: Token) -> bool:
    # No space at string-literal quotes or around common punctuation
    if prev.value.endswith('"') or cur.value.startswith('"'):
        return False
    if prev.value and prev.value[-1] in '([{|,':
        return False
    if cur.value and cur.value[0] in ')]}|,:':
        return False
    # Insert when alnum-ish touches alnum-ish (keywords, names, numbers)
    return (prev.value and prev.value[-1].isalnum()) and (cur.value and cur.value[0].isalnum())

def pretty_with_spaces(s: str) -> str:
    toks = list(gen.lex(s, dont_ignore=True))  # include ignored tokens positions
    # Drop ignored tokens entirely; we’ll add our own spaces
    toks = [t for t in toks if t.type not in getattr(gen, "ignore_tokens", ())]
    out = []
    for i, t in enumerate(toks):
        if i:
            if needs_space(toks[i-1], t):
                out.append(" ")
        out.append(t.value)
    return "".join(out)

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

explicit = make_explicit(gen, base_explicit)

# Optional: see what terminals exist (so you can confirm mangled names)
# print(sorted(n for n in {t.name for t in gen.grammar.terminals}
#              if any(k in n for k in ["SAMPLE_STRING","VOWEL_STRING","SCALE_STRING","PARAM_STRING","BUS_STRING","INT","DOUBLE"])))

# Keep the alphabet readable and also EXCLUDE '/' and '*' so ignored C-style comments won't appear
alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-'\"()"
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
    .filter(lambda s: len(s) > 20)
    .filter(parses_ok)
    .filter(no_empty_cp_list)
)

# Trees if you want them
cp_trees = cp_strings.map(earley.parse)

# --- Try one example (fine for exploration) ---
raw = cp_strings.example()
pretty = pretty_with_spaces(raw)
print(pretty)
print(earley.parse(pretty).pretty())

# def tree_depth(t) -> int:
#     if not hasattr(t, "children"):  # token
#         return 1
#     return 1 + max((tree_depth(c) for c in t.children), default=0)

# min_d, max_d = 6, 16  # tune these
# cp_trees = cp_strings.map(earley.parse).filter(lambda t: min_d <= tree_depth(t) <= max_d)

# # If you want the *string* back, pretty-print after:
# cp_nice = cp_trees.map(lambda t: pretty_with_spaces(Reconstructor(earley).reconstruct(t)))

# from hypothesis import settings, Phase, HealthCheck

# # with settings(
# #     phases=(Phase.generate,),      # disable shrinking (more variety)
# #     database=None,
# #     suppress_health_check=[HealthCheck.filter_too_much],
# # ):
# example = cp_nice.example()
# pretty = pretty_with_spaces(example)
# print(pretty)
# print(earley.parse(pretty).pretty())


# example = cp_strings.example()
# print(example)
# print(earley.parse(example).pretty())