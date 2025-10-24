from dataclasses import dataclass

@dataclass
class ParseError:
    message: str
    line: int
    col: int

class ErrorLog:
    def __init__(self):
        self.items = []

    def add(self, err: ParseError):
        self.items.append(err)

    def as_list(self):
        return [f"L{e.line}:C{e.col} - {e.message}" for e in self.items]

    def has_errors(self):
        return len(self.items) > 0
