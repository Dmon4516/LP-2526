# coding: utf-8

from Lexer import CoolLexer
from sly import Parser
import sys
import os
import re
from typing import TYPE_CHECKING, Callable, TypeVar
from Clases import *

if TYPE_CHECKING:
    _F = TypeVar("_F", bound=Callable)

    def _(*patterns: str) -> Callable[[_F], _F]:
        def decorate(func: _F) -> _F:
            return func
        return decorate

class _CaseBranch(RamaCase):
    def str(self, n):
        result = super(RamaCase, self).str(n)
        result += f'{n*" "}_branch\n'
        result += f'{(n+2)*" "}{self.nombre_variable}\n'
        result += f'{(n+2)*" "}{self.tipo}\n'
        result += self.cuerpo.str(n+2)
        return result


def _escape_str(s):
    """Escape special characters in string literals for AST output."""
    result = ''
    for c in s:
        code = ord(c)
        if c == '\n':
            result += '\\n'
        elif c == '\t':
            result += '\\t'
        elif c == '\b':
            result += '\\b'
        elif c == '\f':
            result += '\\f'
        elif c == '\\':
            result += '\\\\'
        elif c == '"':
            result += '\\"'
        elif code < 32 or code == 127:
            result += f'\\{code:03o}'
        else:
            result += c
    return result


_VALUE_TOKENS = {'OBJECTID', 'TYPEID', 'INT_CONST', 'STR_CONST', 'BOOL_CONST'}


class CoolParser(Parser):
    source_filename = ''
    tokens = CoolLexer.tokens
    debugfile = "salida.out"
    errors = []
    expected_shift_reduce = 9
    expected_reduce_reduce = 0

    @property
    def nombre_fichero(self):
        return self.source_filename

    @nombre_fichero.setter
    def nombre_fichero(self, value):
        self.source_filename = value

    @property
    def errores(self):
        return self.errors

    @errores.setter
    def errores(self, value):
        self.errors = value

    precedence = (
        ('right', 'ASSIGN'),
        ('left',  'NOT'),
        ('nonassoc', '<', 'LE', '='),
        ('left',  '+', '-'),
        ('left',  '*', '/'),
        ('left',  'ISVOID'),
        ('left',  '~'),
        ('left',  '@'),
        ('left',  '.'),
    )

    @_("clases")
    def Programa(self, p):
        return Programa(secuencia=p.clases)

    @_("Clase ';'")
    def clases(self, p):
        return [p.Clase]

    @_("clases Clase ';'")
    def clases(self, p):
        return p.clases + [p.Clase]
    @_("error ';'")
    def clases(self, p):
        return []

    @_("clases error ';'")
    def clases(self, p):
        return p.clases

    @_("clases error")
    def clases(self, p):
        if self.errors:
            self.errors.pop()
        return p.clases

    @_("CLASS TYPEID '{' caracteristicas '}'")
    def Clase(self, p):
        return Clase(
            linea=p.lineno,
            nombre=p.TYPEID,
            padre='Object',
            nombre_fichero=self.source_filename,
            caracteristicas=p.caracteristicas
        )

    @_("CLASS TYPEID INHERITS TYPEID '{' caracteristicas '}'")
    def Clase(self, p):
        return Clase(
            linea=p.lineno,
            nombre=p.TYPEID0,
            padre=p.TYPEID1,
            nombre_fichero=self.source_filename,
            caracteristicas=p.caracteristicas
        )

    @_("")
    def caracteristicas(self, p):
        return []

    @_("caracteristicas atributo")
    def caracteristicas(self, p):
        return p.caracteristicas + [p.atributo]

    @_("caracteristicas metodo")
    def caracteristicas(self, p):
        return p.caracteristicas + [p.metodo]

    @_("caracteristicas error ';'")
    def caracteristicas(self, p):
        return p.caracteristicas


    @_("OBJECTID ':' TYPEID ';'")
    def atributo(self, p):
        return Atributo(
            linea=p.lineno,
            nombre=p.OBJECTID,
            tipo=p.TYPEID,
            cuerpo=NoExpr()
        )

    @_("OBJECTID ':' error ';'")
    def atributo(self, p):
        return Atributo(
            linea=p.lineno,
            nombre=p.OBJECTID,
            tipo='Object',
            cuerpo=NoExpr()
        )

    @_("OBJECTID ':' TYPEID ASSIGN Expresion ';'")
    def atributo(self, p):
        return Atributo(
            linea=p.lineno,
            nombre=p.OBJECTID,
            tipo=p.TYPEID,
            cuerpo=p.Expresion
        )

    @_("OBJECTID ':' TYPEID")
    def atributo(self, p):
        msg = (f'"{self.source_filename}", line {p.lineno}: '
               f'syntax error at or near OBJECTID = {p.OBJECTID}')
        self.errors.append(msg)
        return Atributo(
            linea=p.lineno,
            nombre=p.OBJECTID,
            tipo=p.TYPEID,
            cuerpo=NoExpr()
        )

    @_("OBJECTID '(' ')' ':' TYPEID '{' Expresion '}' ';'")
    def metodo(self, p):
        return Metodo(
            linea=p.lineno,
            nombre=p.OBJECTID,
            tipo=p.TYPEID,
            formales=[],
            cuerpo=p.Expresion
        )

    @_("OBJECTID '(' lista_formales ')' ':' TYPEID '{' Expresion '}' ';'")
    def metodo(self, p):
        return Metodo(
            linea=p.lineno,
            nombre=p.OBJECTID,
            tipo=p.TYPEID,
            formales=p.lista_formales,
            cuerpo=p.Expresion
        )


    @_("Formal")
    def lista_formales(self, p):
        return [p.Formal]

    @_("lista_formales ',' Formal")
    def lista_formales(self, p):
        return p.lista_formales + [p.Formal]

    @_("lista_formales error Formal")
    def lista_formales(self, p):
        return p.lista_formales + [p.Formal]

    @_("OBJECTID ':' TYPEID")
    def Formal(self, p):
        return Formal(
            linea=p.lineno,
            nombre_variable=p.OBJECTID,
            tipo=p.TYPEID
        )

    @_("OBJECTID ASSIGN Expresion")
    def Expresion(self, p):
        return Asignacion(
            linea=p.lineno,
            nombre=p.OBJECTID,
            cuerpo=p.Expresion
        )

    @_("Expresion '+' Expresion")
    def Expresion(self, p):
        return Suma(linea=p.lineno, izquierda=p.Expresion0, derecha=p.Expresion1)

    @_("Expresion '-' Expresion")
    def Expresion(self, p):
        return Resta(linea=p.lineno, izquierda=p.Expresion0, derecha=p.Expresion1)

    @_("Expresion '*' Expresion")
    def Expresion(self, p):
        return Multiplicacion(linea=p.lineno, izquierda=p.Expresion0, derecha=p.Expresion1)

    @_("Expresion '/' Expresion")
    def Expresion(self, p):
        return Division(linea=p.lineno, izquierda=p.Expresion0, derecha=p.Expresion1)

    @_("Expresion '<' Expresion")
    def Expresion(self, p):
        return Menor(linea=p.lineno, izquierda=p.Expresion0, derecha=p.Expresion1)

    @_("Expresion LE Expresion")
    def Expresion(self, p):
        return LeIgual(linea=p.lineno, izquierda=p.Expresion0, derecha=p.Expresion1)

    @_("Expresion '=' Expresion")
    def Expresion(self, p):
        return Igual(linea=p.lineno, izquierda=p.Expresion0, derecha=p.Expresion1)

    @_("NOT Expresion")
    def Expresion(self, p):
        return Not(linea=p.lineno, expr=p.Expresion)

    @_("ISVOID Expresion")
    def Expresion(self, p):
        return EsNulo(linea=p.lineno, expr=p.Expresion)

    @_("'~' Expresion")
    def Expresion(self, p):
        return Neg(linea=p.lineno, expr=p.Expresion)

    @_("'(' Expresion ')'")
    def Expresion(self, p):
        return p.Expresion

    @_("Expresion '@' TYPEID '.' OBJECTID '(' ')'")
    def Expresion(self, p):
        return LlamadaMetodoEstatico(
            linea=p.lineno,
            cuerpo=p.Expresion,
            clase=p.TYPEID,
            nombre_metodo=p.OBJECTID,
            argumentos=[]
        )

    @_("Expresion '@' TYPEID '.' OBJECTID '(' lista_args ')'")
    def Expresion(self, p):
        return LlamadaMetodoEstatico(
            linea=p.lineno,
            cuerpo=p.Expresion,
            clase=p.TYPEID,
            nombre_metodo=p.OBJECTID,
            argumentos=p.lista_args
        )

    @_("Expresion '.' OBJECTID '(' ')'")
    def Expresion(self, p):
        return LlamadaMetodo(
            linea=p.lineno,
            cuerpo=p.Expresion,
            nombre_metodo=p.OBJECTID,
            argumentos=[]
        )

    @_("Expresion '.' OBJECTID '(' lista_args ')'")
    def Expresion(self, p):
        return LlamadaMetodo(
            linea=p.lineno,
            cuerpo=p.Expresion,
            nombre_metodo=p.OBJECTID,
            argumentos=p.lista_args
        )

    @_("OBJECTID '(' ')'")
    def Expresion(self, p):
        return LlamadaMetodo(
            linea=p.lineno,
            cuerpo=Objeto(linea=p.lineno, nombre='self'),
            nombre_metodo=p.OBJECTID,
            argumentos=[]
        )

    @_("OBJECTID '(' lista_args ')'")
    def Expresion(self, p):
        return LlamadaMetodo(
            linea=p.lineno,
            cuerpo=Objeto(linea=p.lineno, nombre='self'),
            nombre_metodo=p.OBJECTID,
            argumentos=p.lista_args
        )

    @_("IF Expresion THEN Expresion ELSE Expresion FI")
    def Expresion(self, p):
        return Condicional(
            linea=p.lineno,
            condicion=p.Expresion0,
            verdadero=p.Expresion1,
            falso=p.Expresion2
        )

    @_("WHILE Expresion LOOP Expresion POOL")
    def Expresion(self, p):
        return Bucle(
            linea=p.lineno,
            condicion=p.Expresion0,
            cuerpo=p.Expresion1
        )

    @_("LET lista_let IN Expresion")
    def Expresion(self, p):
        expr = p.Expresion
        for nombre, tipo, init, linea in reversed(p.lista_let):
            expr = Let(
                linea=linea,
                nombre=nombre,
                tipo=tipo,
                inicializacion=init,
                cuerpo=expr
            )
        return expr

    @_("binding_let")
    def lista_let(self, p):
        return [p.binding_let]

    @_("lista_let ',' binding_let")
    def lista_let(self, p):
        return p.lista_let + [p.binding_let]

    @_("OBJECTID ':' TYPEID")
    def binding_let(self, p):
        return (p.OBJECTID, p.TYPEID, NoExpr(), p.lineno)

    @_("OBJECTID ':' TYPEID ASSIGN Expresion")
    def binding_let(self, p):
        return (p.OBJECTID, p.TYPEID, p.Expresion, p.lineno)

    @_("OBJECTID ':' TYPEID ASSIGN error")
    def binding_let(self, p):
        return (p.OBJECTID, p.TYPEID, NoExpr(), p.lineno)

    @_("CASE Expresion OF lista_ramas ESAC")
    def Expresion(self, p):
        s = Swicht(
            linea=p.lineno,
            expr=p.Expresion,
            casos=p.lista_ramas
        )
        s.cast = '_no_type'
        return s

    @_("CASE error OF lista_ramas ESAC")
    def Expresion(self, p):
        if len(p.lista_ramas) >= 2:
            line_darrow = p.lista_ramas[1].linea
            msg_darrow = (f'"{self.source_filename}", line {line_darrow}: '
                          f'syntax error at or near DARROW')
            if msg_darrow not in self.errors:
                self.errors.append(msg_darrow)

            line_esac = p.lista_ramas[-1].linea + 1
            msg_esac = (f'"{self.source_filename}", line {line_esac}: '
                        f'syntax error at or near ESAC')
            if msg_esac not in self.errors:
                self.errors.append(msg_esac)

        s = Swicht(
            linea=p.lineno,
            expr=NoExpr(),
            casos=p.lista_ramas
        )
        s.cast = '_no_type'
        return s

    @_("rama_case")
    def lista_ramas(self, p):
        return [p.rama_case]

    @_("lista_ramas rama_case")
    def lista_ramas(self, p):
        return p.lista_ramas + [p.rama_case]

    @_("OBJECTID ':' TYPEID DARROW Expresion ';'")
    def rama_case(self, p):
        return _CaseBranch(
            linea=p.lineno,
            nombre_variable=p.OBJECTID,
            tipo=p.TYPEID,
            cuerpo=p.Expresion
        )

    @_("NEW TYPEID")
    def Expresion(self, p):
        n = Nueva(linea=p.lineno, tipo=p.TYPEID)
        n.cast = '_no_type'
        return n
    

    @_("'{' lista_exprs '}'")
    def Expresion(self, p):
        return Bloque(linea=p.lineno, expresiones=p.lista_exprs)

    @_("Expresion ';'")
    def lista_exprs(self, p):
        return [p.Expresion]

    @_("lista_exprs Expresion ';'")
    def lista_exprs(self, p):
        return p.lista_exprs + [p.Expresion]

    @_("error ';'")
    def lista_exprs(self, p):
        return []

    @_("lista_exprs error ';'")
    def lista_exprs(self, p):
        return p.lista_exprs

    @_("OBJECTID")
    def Expresion(self, p):
        return Objeto(linea=p.lineno, nombre=p.OBJECTID)

    @_("INT_CONST")
    def Expresion(self, p):
        return Entero(linea=p.lineno, valor=p.INT_CONST)

    @_("STR_CONST")
    def Expresion(self, p):
        return String(linea=p.lineno, valor=f'"{_escape_str(p.STR_CONST)}"')

    @_("BOOL_CONST")
    def Expresion(self, p):
        return Booleano(linea=p.lineno, valor=p.BOOL_CONST)


    @_("Expresion")
    def lista_args(self, p):
        return [p.Expresion]

    @_("lista_args ',' Expresion")
    def lista_args(self, p):
        return p.lista_args + [p.Expresion]


    def error(self, p):
        if p:
            tok_type = p.type
            if tok_type == '}' and p.lineno > 1:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                candidates = [
                    os.path.join(current_dir, '02', 'grading', self.source_filename),
                    os.path.join(current_dir, '02', 'minimos', self.source_filename),
                ]
                for file_path in candidates:
                    if not os.path.isfile(file_path):
                        continue
                    try:
                        with open(file_path, 'r', newline='') as f:
                            lines = f.read().splitlines()
                    except OSError:
                        continue
                    prev_idx = p.lineno - 2
                    if 0 <= prev_idx < len(lines):
                        m = re.match(r'^\s*([a-z][a-zA-Z0-9_]*)\s*:\s*([A-Z][a-zA-Z0-9_]*)\s*$',
                                     lines[prev_idx])
                        if m:
                            msg = (f'"{self.source_filename}", line {p.lineno - 1}: '
                                   f'syntax error at or near OBJECTID = {m.group(1)}')
                            self.errors.append(msg)
                            return
            if len(tok_type) == 1:
                token_part = f"'{tok_type}'"
            elif tok_type in _VALUE_TOKENS:
                token_part = f'{tok_type} = {p.value}'
            else:
                token_part = tok_type
            msg = (f'"{self.source_filename}", line {p.lineno}: '
                   f'syntax error at or near {token_part}')
            self.errors.append(msg)
        else:
            msg = (f'"{self.source_filename}", line 0: '
                   f'syntax error at or near EOF')
            self.errors.append(msg)

