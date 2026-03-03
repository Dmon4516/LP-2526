# coding: utf-8

from sly import Lexer
import os
import re
import sys

from typing import TYPE_CHECKING, Callable, TypeVar

if TYPE_CHECKING:
    _F = TypeVar("_F", bound=Callable)

    def _(*patterns: str) -> Callable[[_F], _F]:
        def decorate(func: _F) -> _F:
            return func
        return decorate

class Comentario(Lexer):
    tokens = {}
    # TODO: Implementar contador de nesting para comentarios anidados
    # nested = 1  # iniciar en 1 cuando se entra a Comentario
    nested = 0  # iniciar en 0, incrementar al entrar a Comentario, decrementar al salir
    ignore = ''
    
    @_(r'.')
    def PASAR(self, t):
        pass
    @_(r'\n')
    def LINEA(self, t):
        self.lineno += 1
    @_(r'\*\)')
    def VOLVER(self, t):
        if self.nested == 1:
            self.begin(CoolLexer)
        else:
            self.nested -= 1




class CoolLexer(Lexer):
    tokens = {
        'OBJECTID', 'INT_CONST', 'BOOL_CONST', 'TYPEID',
        'ELSE', 'IF', 'FI', 'THEN', 'NOT', 'IN', 'CASE', 'ESAC', 'CLASS',
        'INHERITS', 'ISVOID', 'LET', 'LOOP', 'NEW', 'OF',
        'POOL', 'WHILE', 'STR_CONST', 'LE', 'DARROW', 'ASSIGN', 'SPACE'
    }
    ignore = '\t '

    @_(r'--.*')
    def COMMENT(self, t):
        self.lineno += 1
    
    @_(r'[<][=]')
    def LE(self, t):
        return t
    
    @_(r'[<][-]')
    def ASSIGN(self, t):
        return t
    
    @_(r'[=][>]')
    def DARROW(self, t):
        return t
    
    @_(r'\b[t][r][u][e]\b|\b[f][a][l][s][e]\b')
    def BOOL_CONST(self, t):
        if t.value == 'true':
            t.value = True
        elif t.value == 'false':            
            t.value = False
        return t

    literals = {
        '+', '-', '*', '/', '(', ')',
        '<', '=', '.', ',', ';', ':',
        '@', '{', '}', '>', '~', 
    }

    string_escapes = {
        '\\b', '\b',
        '\\t', '\t',
        '\\n', '\n',
        '\\r', '\r',
    }

    
    @_(r'[a-z][A-Z0-9_a-z]*')
    def OBJECTID(self, t):
        palabras_reservadas = {'else', 'if', 'fi', 'then', 'not', 'in', 'case', 'esac', 'class', 'inherits', 'isvoid', 'let', 'loop', 'new', 'of', 'pool', 'while', 'true', 'false'}
        if t.value.lower() in palabras_reservadas:
            t.type = t.value.upper()
            # TODO: Verificar si verdadero es solo si la forma es 'true' o 'false' en minúscula
            # Si es 'TRUE' o 'FALSE' debe ser TYPEID, no BOOL_CONST
        return t
    
    @_(r'\b\d+\b')
    def INT_CONST(self, t):
        return t
    
    @_(r'\s+')
    def SPACE(self, t):
        return t
    
    @_(r'\b[A-Z][A-Za-z0-9_]*\b')
    def TYPEID(self, t):
        return t
    
    @_(r'\n')
    def LINEBREAK(self, t):
        self.lineno += 1
    
    @_(r'"([^"\\]|\\.)*"')
    def STR_CONST(self, t):
        # TODO: Procesar escapes: \\b -> \b, \\t -> \t, \\n -> \n, \\r -> \r
        # TODO: Validar longitud máxima 1024 caracteres
        # TODO: Rechazar si contiene: \0, EOF, o saltos de línea sin escape
        # TODO: Quitar las comillas del valor final
        if t.value == self.string_escapes:
            return t
    
    

    def error(self, t):
        t.type = 'ERROR'
        t.value = t.value[0]
        self.lineno += 1
        return t

    CARACTERES_CONTROL = [bytes.fromhex(i+hex(j)[-1]).decode('ascii')
                          for i in ['0', '1']
                          for j in range(16)] + [bytes.fromhex(hex(127)[-2:]).decode("ascii")]

    # TODO: Implementar patrón para comentarios anidados sin contar los escapados
    # @_(r'\(\*[^\\]\)')
    @_(r'\(\*')
    def IR(self, t):
        # Iniciar estado de comentario anidado
        self.begin(Comentario)
        
    def salida(self, texto):
        # TODO: Revisar formato de salida con los archivos de ejemplo
        # TODO: Verificar que STR_CONST y otros tokens tengan el formato correcto
        lexer = CoolLexer()
        list_strings = []
        for token in lexer.tokenize(texto):
            result = f'#{token.lineno} {token.type} '
            if token.type == 'OBJECTID':
                result += f"{token.value}"
            elif token.type == 'BOOL_CONST':
                result += "true" if token.value else "false"
            elif token.type == 'TYPEID':
                result += f"{str(token.value)}"
            elif token.type in self.literals:
                result = f'#{token.lineno} \'{token.type}\' '
            elif token.type == 'STR_CONST':
                result += token.value
            elif token.type == 'INT_CONST':
                result += str(token.value)
            elif token.type == 'ERROR':
                result = f'#{token.lineno} {token.type} {token.value}'
            else:
                result = f'#{token.lineno} {token.type}'
            list_strings.append(result)
        return list_strings
