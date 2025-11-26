import re
from enum import Enum
from dataclasses import dataclass
from .errors import LexError  # <-- nueva importación

# Analizador léxico simple para un subconjunto de SQL.
#
# Exporta:
#  - TokenType: Enum de tipos de token (RESWORD, IDENT, NUMBER, STRING, SYMBOL, OP, EOF)
#  - Token: dataclass con {type, value, line, col}
#  - Lexer: clase que tokeniza una cadena SQL con `tokenize()`
#
# Notas de implementación:
#  - `RESWORDS` contiene palabras reservadas soportadas (se comparan en uppercase).
#  - `token_regex` captura espacios, comentarios (--), identificadores, números, strings, operadores y símbolos.
#  - El lexer emite tokens con posición (línea/columna) y añade un EOF final.
#  - Revisar patrones y grupos de captura si se añaden nuevos símbolos/operadores.


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
    "NULL","INT","VARCHAR","FLOAT","AND","OR","NOT"
}

SYMBOLS = {',',';','(',')','*','.'}
OPS      = {'=','<','>','<=','>=','<>'}


@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    col: int


class Lexer:
    token_regex = re.compile(
        r"\s+|"                                
        r"(--[^\n]*)|"                          
        r"([A-Za-z_][A-Za-z0-9_]*)|"            
        r"(\d+(?:\.\d+)?)|"                     
        r"('([^']*)')"                          
        r"|(\<=|\>=|<>|=|<|>)|"                 
        r"([,;\(\)\*\.\+])"                     
    )

    def __init__(self, text: str):
        self.text = text
        self.line = 1
        self.col = 1
        self.tokens = []
        self.lex_errors = []

    def _emit(self, t: Token):
        self.tokens.append(t)

    def tokenize(self):
        i = 0

        while i < len(self.text):
            m = self.token_regex.match(self.text, i)
            if not m:
                # STRING SIN CERRAR
                if self.text[i] == "'":
                    self.lex_errors.append(LexError(
                        "String sin cerrar", self.line, self.col
                    ))
                    j = self.text.find("\n", i)
                    if j == -1:
                        break
                    i = j + 1
                    self.line += 1
                    self.col = 1
                    continue

                # CARÁCTER DESCONOCIDO
                val = self.text[i]
                self.lex_errors.append(
                    LexError(f"Carácter no reconocido: '{val}'", self.line, self.col)
                )
                i += 1
                self.col += 1
                continue

            val = m.group(0)
            newlines = val.count("\n")

            if newlines:
                self.line += newlines
                self.col = 1 + len(val) - val.rfind("\n") - 1
            else:
                self.col += len(val)

            i = m.end()

            if m.group(1):
                continue

            if m.group(2):
                up = m.group(2).upper()
                if up in RESWORDS:
                    self._emit(Token(TokenType.RESWORD, up, self.line, self.col - len(val)))
                else:
                    self._emit(Token(TokenType.IDENT, m.group(2), self.line, self.col - len(val)))
                continue

            if m.group(3):
                self._emit(Token(TokenType.NUMBER, m.group(3), self.line, self.col - len(val)))
                continue

            if m.group(4):
                self._emit(Token(TokenType.STRING, m.group(4), self.line, self.col - len(val)))
                continue

            if m.group(6):
                self._emit(Token(TokenType.OP, m.group(6), self.line, self.col - len(val)))
                continue

            if m.group(7):
                s = m.group(7)
                if s in SYMBOLS:
                    self._emit(Token(TokenType.SYMBOL, s, self.line, self.col - len(val)))
                else:
                    self.lex_errors.append(LexError(
                        f"Símbolo no permitido: '{s}'",
                        self.line,
                        self.col - len(val)
                    ))
                continue

        self._emit(Token(TokenType.EOF, "", self.line, self.col))
        return self.tokens
