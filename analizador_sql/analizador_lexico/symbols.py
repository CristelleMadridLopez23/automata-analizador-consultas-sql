import hashlib
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict

# Implementación simple de tabla de símbolos basada en hashing.
#
# Exporta:
#  - SymKind: Enum con tipos de entrada (RESWORD, TABLE, COLUMN, IDENT, LITERAL, OP, TYPE, TYPEARG, EOF)
#  - SymEntry: dataclass que representa una entrada de la tabla de símbolos
#  - SymbolTable: clase con buckets, add(), entries(), stats()
#
# Notas:
#  - El hash se calcula con md5 de la tupla (kind:value:line:col)
#  - `add()` incrementa refs si la entrada ya existe en el bucket
#  - `stats()` devuelve colisiones y recuentos por tipo


class SymKind(Enum):
    RESWORD = "RESWORD"
    TABLE   = "TABLE"
    COLUMN  = "COLUMN"
    IDENT   = "IDENT"
    LITERAL = "LITERAL"
    OP      = "OP"
    TYPE    = "TYPE"
    TYPEARG = "TYPEARG"
    EOF     = "EOF"


@dataclass
class SymEntry:
    idx: int      # <--- Agregamos este campo para guardar el índice del bucket
    hash: str
    kind: SymKind
    value: str
    line: int
    col: int
    refs: int = 1


class SymbolTable:
    def __init__(self, size=1024):
        self.size = size
        self.buckets: List[List[SymEntry]] = [[] for _ in range(size)]
        self.total = 0

    def _idx(self, code: str) -> int:
        return int(code[:8], 16) % self.size

    def add(self, token, kind: SymKind):
        raw = token.value.lower()
        h = hashlib.md5(raw.encode()).hexdigest()
        idx = self._idx(h)

        for entry in self.buckets[idx]:
            if entry.hash == h:
                entry.refs += 1
                # CORRECCIÓN: Si ya existe como IDENT pero ahora sabemos que es algo más específico
                # (TABLE, COLUMN, TYPE, etc.), actualizamos su tipo.
                if entry.kind == SymKind.IDENT and kind != SymKind.IDENT:
                    entry.kind = kind
                return

        self.buckets[idx].append(
            SymEntry(
                idx=idx,  # Ahora esto funcionará correctamente
                hash=h,
                kind=kind,
                value=token.value,
                line=token.line,
                col=token.col,
            )
        )
        self.total += 1

    def entries(self):
        out = []
        for b in self.buckets:
            out.extend(b)
        return out

    def stats(self):
        collisions = sum(max(0, len(b) - 1) for b in self.buckets)
        by_kind = {}
        for e in self.entries():
            by_kind[e.kind.value] = by_kind.get(e.kind.value, 0) + 1

        return {
            "size": self.size,
            "total_entries": self.total,
            "collisions": collisions,
            "load_factor": round(self.total / self.size, 4),
            "by_kind": by_kind,
        }
