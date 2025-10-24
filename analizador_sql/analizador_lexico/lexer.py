import re
from enum import Enum
from dataclasses import dataclass

class TokenType(Enum):
    RESWORD = "RESWORD"
    IDENT   = "IDENT"
    NUMBER  = "NUMBER"
    STRING  = "STRING"
    SYMBOL  = "SYMBOL"
    OP      = "OP"
    EOF     = "EOF"

RESWORDS = {
    "SELECT","FROM","WHERE","INSERT","INTO","VALUES",
    "UPDATE","SET","CREATE","TABLE","PRIMARY","KEY",
    "NULL","INT","VARCHAR","FLOAT"
}

SYMBOLS = {',',';','(',')','*','.'}
OPS     = {'=','<','>','<=','>=','<>'}

@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    col: int

class Lexer:
    token_regex = re.compile(
        r"\s+|"                                 # espacios
        r"(--[^\n]*)|"                           # comentarios línea -- ...
        r"([A-Za-z_][A-Za-z0-9_]*)|"             # ident o resword
        r"(\d+(?:\.\d+)?)|"                      # number
        r"('([^']*)')"                           # 'string'
        r"|(\<=|\>=|<>|=|<|>)|"                  # operadores
        r"([,;\(\)\*\.\+])"                      # símbolos
    )

    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens = []

    def _emit(self, t: Token):
        self.tokens.append(t)

    def tokenize(self):
        i = 0
        while i < len(self.text):
            m = self.token_regex.match(self.text, i)
            if not m:
                # carácter no reconocido
                val = self.text[i]
                self._emit(Token(TokenType.SYMBOL, val, self.line, self.col))
                i += 1
                self.col += 1
                continue

            val = m.group(0)
            # manejar saltos de línea en espacios o comentarios
            newlines = val.count("\n")
            if newlines:
                self.line += newlines
                self.col = 1 + len(val) - val.rfind("\n") - 1
            else:
                self.col += len(val)

            i = m.end()

            if m.group(1):   # comentario
                continue
            if m.group(2):   # ident
                up = m.group(2).upper()
                if up in RESWORDS:
                    self._emit(Token(TokenType.RESWORD, up, self.line, self.col - len(val)))
                else:
                    self._emit(Token(TokenType.IDENT, m.group(2), self.line, self.col - len(val)))
                continue
            if m.group(3):   # number
                self._emit(Token(TokenType.NUMBER, m.group(3), self.line, self.col - len(val)))
                continue
            if m.group(4):   # string
                self._emit(Token(TokenType.STRING, m.group(4), self.line, self.col - len(val)))
                continue
            if m.group(6):   # op
                self._emit(Token(TokenType.OP, m.group(6), self.line, self.col - len(val)))
                continue
            if m.group(7):   # symbol
                sym = m.group(7)
                if sym in SYMBOLS:
                    self._emit(Token(TokenType.SYMBOL, sym, self.line, self.col - len(val)))
                else:
                    self._emit(Token(TokenType.SYMBOL, sym, self.line, self.col - len(val)))
                continue

        self._emit(Token(TokenType.EOF, "", self.line, self.col))
        return self.tokens
