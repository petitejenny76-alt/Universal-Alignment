from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class RootOfTrust:
    expected_constitution_hash: str

    @classmethod
    def from_hash_file(cls, path: str):
        value = Path(path).read_text(encoding="utf-8").strip().split()[0]
        if len(value) != 64:
            raise ValueError("invalid_constitution_hash")
        return cls(expected_constitution_hash=value)
