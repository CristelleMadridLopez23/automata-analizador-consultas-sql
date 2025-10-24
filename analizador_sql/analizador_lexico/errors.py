from dataclasses import dataclass

# Definición simple de errores de parsing.
#
# - ParseError: dataclass con message, line, col
# - ErrorLog: acumulador con `add()`, `as_list()`, `has_errors()`
#
# Uso: el Parser agrega ParseError a ErrorLog; la vista transforma a lista con as_list().

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
