# Lenguajes Formales y Automatas-Analizador de Consultas SQL

Analizador léxico y sistema de validación de un subconjunto de consultas SQL basado en autómatas/gramáticas.
Proyecto educativo que implementa:
- Un lexer que tokeniza SELECT/INSERT/UPDATE/CREATE (y tipos básicos).
- Un parser recursivo predictivo que valida la gramática y construye una tabla de símbolos.
- Una tabla de símbolos simple basada en hashing y un registro de errores.

## Estructura
- analizador_sql/ : proyecto Django
  - analizador_lexico/ : app principal con lexer, parser, símbolos y vistas
    - lexer.py : tokenizador
    - parser.py : parser y reglas (BNF reducida)
    - symbols.py : tabla de símbolos (hash)
    - errors.py : manejo de errores de parseo
    - templates/index.html : UI para subir archivos .sql
- test_data/ : archivos de consulta de ejemplo (válidas y con errores)

## Pruebas
- Añadir tests en `analizador_lexico/tests.py` y ejecutar:
  - python manage.py test

## Desarrollo / Mejora
- Expandir el conjunto de palabras reservadas y operadores en `analizador_lexico/lexer.py`.
- Mejorar el manejo de strings con comillas escapadas.
- Añadir logging y trazas más detalladas en `views.index`.
- Persistir resultados (tabla de símbolos, errores) en modelos Django si se requiere histórico.
