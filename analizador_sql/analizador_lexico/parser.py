from .lexer import TokenType
from .symbols import SymbolTable, SymKind
from .errors import ErrorLog, ParseError

class Parser:
    def __init__(self, tokens, symtab: SymbolTable, errlog: ErrorLog, progress):
        self.toks = tokens
        self.i = 0
        self.symtab = symtab
        self.errlog = errlog
        self.progress = progress  # lista de strings para “log en vivo”

    def t(self):  # token actual
        return self.toks[self.i]

    def eat(self, kind, values=None):
        tk = self.t()
        if tk.type == kind and (values is None or tk.value in values):
            self.i += 1
            return tk
        exp = f"{kind.name}" + (f" {values}" if values else "")
        self.errlog.add(ParseError(f"Se esperaba {exp}, se encontró '{tk.value}'", tk.line, tk.col))
        # intento de sincronización: avanzar uno
        self.i += 1
        return tk

    def program(self):
        self.progress.append("Iniciando análisis del programa…")
        while self.t().type != TokenType.EOF:
            self.stmt()
            # opcionalmente comer ';' si existe
            if self.t().value == ';':
                self.eat(TokenType.SYMBOL, {';'})
        self.progress.append("Análisis finalizado.")

    # STMT → SELECT | INSERT | UPDATE | CREATE
    def stmt(self):
        tk = self.t()
        if tk.value == 'SELECT':
            self.select_stmt()
        elif tk.value == 'INSERT':
            self.insert_stmt()
        elif tk.value == 'UPDATE':
            self.update_stmt()
        elif tk.value == 'CREATE':
            self.create_stmt()
        else:
            self.errlog.add(ParseError(f"Sentencia no reconocida: {tk.value}", tk.line, tk.col))
            self.i += 1

    # SELECT_STMT → SELECT COLUMN_LIST FROM IDENT (WHERE COND)?
    def select_stmt(self):
        sel = self.eat(TokenType.RESWORD, {'SELECT'})
        self.symtab.add(sel, SymKind.RESWORD)
        self.column_list()
        self.eat(TokenType.RESWORD, {'FROM'})
        table = self.eat(TokenType.IDENT)
        self.symtab.add(table, SymKind.TABLE)
        if self.t().value == 'WHERE':
            w = self.eat(TokenType.RESWORD, {'WHERE'})
            self.symtab.add(w, SymKind.RESWORD)
            self.cond()

    # COLUMN_LIST → * | IDENT (',' IDENT)*
    def column_list(self):
        if self.t().value == '*':
            self.eat(TokenType.SYMBOL, {'*'})
        else:
            col = self.eat(TokenType.IDENT)
            self.symtab.add(col, SymKind.COLUMN)
            while self.t().value == ',':
                self.eat(TokenType.SYMBOL, {','})
                col = self.eat(TokenType.IDENT)
                self.symtab.add(col, SymKind.COLUMN)

    # COND → IDENT OP (NUMBER | STRING | IDENT)
    def cond(self):
        left = self.eat(TokenType.IDENT)
        self.symtab.add(left, SymKind.COLUMN)
        op = self.eat(TokenType.OP)
        self.symtab.add(op, SymKind.OP)
        if self.t().type in (TokenType.NUMBER, TokenType.STRING):
            lit = self.t(); self.i += 1
            self.symtab.add(lit, SymKind.LITERAL)
        elif self.t().type == TokenType.IDENT:
            idt = self.eat(TokenType.IDENT)
            self.symtab.add(idt, SymKind.IDENT)
        else:
            tk = self.t()
            self.errlog.add(ParseError("Se esperaba literal o identificador en condición", tk.line, tk.col))
            self.i += 1

    # INSERT_STMT → INSERT INTO IDENT '(' IDENT_LIST ')' VALUES '(' LITERAL_LIST ')'
    def insert_stmt(self):
        ins = self.eat(TokenType.RESWORD, {'INSERT'}); self.symtab.add(ins, SymKind.RESWORD)
        self.eat(TokenType.RESWORD, {'INTO'})
        tbl = self.eat(TokenType.IDENT); self.symtab.add(tbl, SymKind.TABLE)
        self.eat(TokenType.SYMBOL, {'('}); self.ident_list(); self.eat(TokenType.SYMBOL, {')'})
        self.eat(TokenType.RESWORD, {'VALUES'})
        self.eat(TokenType.SYMBOL, {'('}); self.literal_list(); self.eat(TokenType.SYMBOL, {')'})

    def ident_list(self):
        idt = self.eat(TokenType.IDENT); self.symtab.add(idt, SymKind.COLUMN)
        while self.t().value == ',':
            self.eat(TokenType.SYMBOL, {','})
            idt = self.eat(TokenType.IDENT); self.symtab.add(idt, SymKind.COLUMN)

    def literal_list(self):
        self.literal()
        while self.t().value == ',':
            self.eat(TokenType.SYMBOL, {','})
            self.literal()

    def literal(self):
        tk = self.t()
        if tk.type in (TokenType.NUMBER, TokenType.STRING):
            self.symtab.add(tk, SymKind.LITERAL); self.i += 1
        elif tk.value == 'NULL':
            self.symtab.add(tk, SymKind.LITERAL); self.i += 1
        else:
            self.errlog.add(ParseError("Literal inválido (NUMBER/STRING/NULL)", tk.line, tk.col)); self.i += 1

    # UPDATE_STMT → UPDATE IDENT SET ASSIGN_LIST (WHERE COND)?
    def update_stmt(self):
        up = self.eat(TokenType.RESWORD, {'UPDATE'}); self.symtab.add(up, SymKind.RESWORD)
        tbl = self.eat(TokenType.IDENT); self.symtab.add(tbl, SymKind.TABLE)
        self.eat(TokenType.RESWORD, {'SET'})
        self.assign_list()
        if self.t().value == 'WHERE':
            w = self.eat(TokenType.RESWORD, {'WHERE'}); self.symtab.add(w, SymKind.RESWORD)
            self.cond()

    def assign_list(self):
        self.assign()
        while self.t().value == ',':
            self.eat(TokenType.SYMBOL, {','})
            self.assign()

    def assign(self):
        col = self.eat(TokenType.IDENT); self.symtab.add(col, SymKind.COLUMN)
        self.eat(TokenType.OP, {'='})
        self.literal()

    # CREATE_STMT → CREATE TABLE IDENT '(' COLDEF_LIST ')'
    def create_stmt(self):
        cr = self.eat(TokenType.RESWORD, {'CREATE'}); self.symtab.add(cr, SymKind.RESWORD)
        self.eat(TokenType.RESWORD, {'TABLE'})
        tbl = self.eat(TokenType.IDENT); self.symtab.add(tbl, SymKind.TABLE)
        self.eat(TokenType.SYMBOL, {'('}); self.coldef_list(); self.eat(TokenType.SYMBOL, {')'})

    def coldef_list(self):
        self.coldef()
        while self.t().value == ',':
            self.eat(TokenType.SYMBOL, {','})
            self.coldef()

    # COLDEF → IDENT TYPE (PRIMARY KEY)?
    def coldef(self):
        col = self.eat(TokenType.IDENT); self.symtab.add(col, SymKind.COLUMN)
        self.type_spec()
        if self.t().value == 'PRIMARY':
            self.eat(TokenType.RESWORD, {'PRIMARY'})
            self.eat(TokenType.RESWORD, {'KEY'})

    # TYPE → INT | VARCHAR '(' NUMBER ')' | FLOAT
    def type_spec(self):
        tk = self.t()
        if tk.value == 'INT' or tk.value == 'FLOAT':
            self.i += 1; self.symtab.add(tk, SymKind.TYPE); return
        if tk.value == 'VARCHAR':
            self.i += 1; self.symtab.add(tk, SymKind.TYPE)
            self.eat(TokenType.SYMBOL, {'('})
            num = self.eat(TokenType.NUMBER); self.symtab.add(num, SymKind.TYPEARG)
            self.eat(TokenType.SYMBOL, {')'})
            return
        self.errlog.add(ParseError("Tipo de dato inválido (INT|FLOAT|VARCHAR(n))", tk.line, tk.col)); self.i += 1
