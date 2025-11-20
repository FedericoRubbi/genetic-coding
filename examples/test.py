from pathlib import Path

from genetic_music.generator.generation import generate_expressions
from genetic_music.codegen.tidal_codegen import to_tidal


def main():
    # Generate a single random control pattern tree
    tree = generate_expressions(1)[0]
    print("Tree:", tree)

    pattern = to_tidal(tree)
    print("Pattern:", pattern)

    # Just ensure we can write it somewhere (no audio backend here)
    output_dir = Path("data/outputs/test")
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "pattern.tidal").write_text(pattern, encoding="utf-8")


if __name__ == "__main__":
    main()