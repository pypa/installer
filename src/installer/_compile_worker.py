import compileall
from typing import Iterable, Sequence


def compile_files(
    optimization_levels: Iterable[int],
    target_and_embed_dirs: Iterable[
        Sequence[str]
    ],  # JSON deserialized content are all lists, so just use Sequence instead of Tuple[str, str]
) -> None:
    """Perform actual compilation work."""
    for file_and_embed_dir in target_and_embed_dirs:
        file, embed_dir = file_and_embed_dir
        for level in optimization_levels:
            # We use ``compileall`` instead of ``py_compile``
            # because ``compileall`` has heuristics to skip files which are not compilable
            compileall.compile_file(file, quiet=1, ddir=embed_dir, optimize=level)


if __name__ == "__main__":
    import json
    import sys

    compile_files(**json.loads(sys.stdin.read()))
