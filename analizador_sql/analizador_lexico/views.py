from django.shortcuts import render
from django.core.files.uploadedfile import UploadedFile
from .lexer import Lexer, TokenType
from .parser import Parser
from .symbols import SymbolTable, SymKind
from .errors import ErrorLog, ParseError

# Vista principal `index` que procesa subida de archivo .sql:
#  - Lee el archivo subido y lo pasa al Lexer -> tokens
#  - Crea SymbolTable y ErrorLog
#  - Ejecuta Parser para validar y llenar tabla de símbolos
#  - Prepara contexto para la plantilla index.html
# Referencias importantes en este archivo:
#  - Lexer: analizador_sql/analizador_lexico/lexer.py
#  - Parser: analizador_sql/analizador_lexico/parser.py
#  - SymbolTable: analizador_sql/analizador_lexico/symbols.py
#  - ErrorLog/ParseError: analizador_sql/analizador_lexico/errors.py

def index(request):
    context = {
        "log": [],
        "errors": [],
        "tokens": [],
        "symtab": [],
        "stats": {},
        "source": "",
        "filename": ""
    }

    if request.method == "POST":
        file: UploadedFile = request.FILES.get("sqlfile")
        if not file:
            context["errors"] = ["Debes seleccionar un archivo .sql"]
            return render(request, "sql_automata/index.html", context)

        data = file.read().decode("utf-8", errors="replace")
        context["source"] = data
        context["filename"] = file.name

        # LEXER + ERRORLOG
        errlog = ErrorLog()
        lx = Lexer(data, errlog)
        tokens = lx.tokenize()
        context["tokens"] = [{"type": t.type.name, "value": t.value, "line": t.line, "col": t.col} for t in tokens[:2000]]

        # SYMBOL TABLE
        symtab = SymbolTable()

        # Agregar EOF a tabla
        eof = next(t for t in tokens if t.type == TokenType.EOF)
        symtab.add(eof, SymKind.EOF)

        # mostrar errores léxicos (sin parser)
        context["errors"] = errlog.as_list()
        context["symtab"] = [{
            "hash": e.hash[:8],
            "kind": e.kind.value,
            "value": e.value,
            "line": e.line,
            "col": e.col,
            "refs": e.refs
        } for e in symtab.entries()]
        context["stats"] = symtab.stats()

    return render(request, "index.html", context)
