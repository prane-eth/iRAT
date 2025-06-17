from dataclasses import dataclass

@dataclass
class CodeStructure:
    id: str
    promt: str
    code: str
    tests: str
