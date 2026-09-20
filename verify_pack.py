"""Verify file hashes and coverage against the unsigned local package manifest.
This detects changes relative to the manifest, not malicious replacement of both.
"""
from hashlib import sha256
import json
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent
    manifest = json.loads((root / "MANIFEST_SHA256.json").read_text(encoding="utf-8"))
    problems = []
    for relative, expected in manifest.items():
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            problems.append("Fichier absent ou chemin invalide : " + relative)
        elif sha256(path.read_bytes()).hexdigest() != expected:
            problems.append("Empreinte différente : " + relative)
    current = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
        and path.name != "MANIFEST_SHA256.json" and path.suffix != ".pyc"
    }
    for relative in sorted(current - set(manifest)):
        problems.append("Fichier non couvert : " + relative)
    if problems:
        print("\n".join(problems))
        return 1
    print(str(len(manifest)) + " fichiers conformes au manifeste non signé.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
