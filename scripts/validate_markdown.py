from pathlib import Path
import subprocess
import sys


def main():
    files = subprocess.check_output(
        ["git", "ls-files", "-z", "--", "*.md"]
    ).decode("utf-8").split("\0")
    errors = []
    for name in filter(None, files):
        path = Path(name)
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"{name}: {exc}")
            continue
        if not content.strip():
            errors.append(f"{name}: arquivo vazio")
        for number, line in enumerate(content.splitlines(), 1):
            if line.startswith(("<<<<<<< ", "=======", ">>>>>>> ")):
                errors.append(f"{name}:{number}: possível conflito de merge")
    if errors:
        print("\n".join(errors))
        return 1
    print(f"{len(list(filter(None, files)))} arquivos Markdown verificados.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
