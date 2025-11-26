from django.shortcuts import render
from django.core.files.uploadedfile import UploadedFile
from .lexer import Lexer, TokenType
from .parser import Parser
from .symbols import SymbolTable, SymKind
from .errors import ErrorLog, ParseError
from .lexer import TokenType

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
        "filename": "",
        "mode": "lex"
    }

    # ==========================================================
    # 1) RECEPCIÓN DEL ARCHIVO O RECUPERACIÓN DE SESIÓN
    # ==========================================================
    if request.method == "POST":
        file: UploadedFile = request.FILES.get("sqlfile")

        if file:
            data = file.read().decode("utf-8", errors="replace")
            request.session["sqlfile_content"] = data
            request.session["sqlfile_name"] = file.name
        else:
            data = request.session.get("sqlfile_content", "")
            file = request.session.get("sqlfile_name", "")

        if not data:
            context["errors"].append("No se recibió archivo ni hay uno almacenado.")
            return render(request, "index.html", context)

        context["source"] = data
        context["filename"] = file if isinstance(file, str) else file.name

        # Modo solicitado
        mode = request.POST.get("mode", "lex")
        context["mode"] = mode

        # ==========================================================
        # 2) EJECUTAR LÉXICO SIEMPRE
        # ==========================================================
        lx = Lexer(data)
        tokens = lx.tokenize()

        context["tokens"] = [
            {"type": t.type.name, "value": t.value, "line": t.line, "col": t.col}
            for t in tokens
        ]

        lex_errors = lx.lex_errors

        context["lex"] = {
            "tokens": context["tokens"],
            "errors": [f"L{e.line}:C{e.col} - {e.message}" for e in lex_errors],
        }

        # ==========================================================
        # 3) CONSTRUIR TABLA DE SÍMBOLOS DEL LÉXICO
        # ==========================================================
        lex_symtab = SymbolTable()

        for t in tokens:
            if t.type == TokenType.RESWORD:
                lex_symtab.add(t, SymKind.RESWORD)
            elif t.type == TokenType.IDENT:
                lex_symtab.add(t, SymKind.IDENT)
            elif t.type in (TokenType.NUMBER, TokenType.STRING):
                lex_symtab.add(t, SymKind.LITERAL)
            elif t.type == TokenType.OP:
                lex_symtab.add(t, SymKind.OP)
            elif t.type == TokenType.EOF:
                lex_symtab.add(t, SymKind.EOF)

        # Exponer tabla de símbolos inicial
        context["symtab"] = [
            {
                "hash": e.hash[:8],
                "kind": e.kind.value,
                "value": e.value,
                "line": e.line,
                "col": e.col,
                "refs": e.refs,
            }
            for e in lex_symtab.entries()
        ]
        context["stats"] = lex_symtab.stats()

        # ==========================================================
        # 4) SI HAY ERRORES LÉXICOS → NO HAY SINTÁCTICO
        # ==========================================================
        if lex_errors:
            context["parse"] = {
                "errors": ["Análisis sintáctico no ejecutado: hay errores léxicos."],
                "symtab": [],
                "stats": {},
                "log": ["Detenido por errores léxicos."]
            }
            return render(request, "index.html", context)

        # ==========================================================
        # 5) MODO LÉXICO → NO EJECUTAR PARSER
        # ==========================================================
        if mode == "lex":
            context["parse"] = {
                "errors": ["Análisis sintáctico no solicitado (modo léxico)."],
                "symtab": [],
                "stats": {},
                "log": ["Modo léxico: parser no ejecutado."]
            }
            return render(request, "index.html", context)

        # ==========================================================
        # 6) EJECUTAR PARSER (usa la misma tabla del léxico)
        # ==========================================================
        errlog = ErrorLog()
        context["log"].append("Iniciando parser…")

        parser = Parser(tokens, lex_symtab, errlog, context["log"])
        parser.program()

        # EOF obligatorio
        eof = next((t for t in tokens if t.type == TokenType.EOF), None)
        if eof:
            lex_symtab.add(eof, SymKind.EOF)

        context["parse"] = {
            "errors": errlog.as_list(),
            "symtab": [
                {
                    "hash": e.hash[:8],
                    "kind": e.kind.value,
                    "value": e.value,
                    "line": e.line,
                    "col": e.col,
                    "refs": e.refs,
                }
                for e in lex_symtab.entries()
            ],
            "stats": lex_symtab.stats(),
            "log": context["log"],
        }

        # Mostrar finalmente la symtab del parser (derivada del léxico)
        context["symtab"] = context["parse"]["symtab"]
        context["stats"] = context["parse"]["stats"]

    return render(request, "index.html", context)

