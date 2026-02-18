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
    @_(r'.')
    def PASAR(self, t):
        pass
    @_(r'\n')
    def LINEA(self, t):
        self.lineno += 1
    @_(r'\*\)')
    def VOLVER(self, t):
        self.begin(CoolLexer)




class CoolLexer(Lexer):
    tokens = {
        'OBJECTID', 'INT_CONST', 'BOOL_CONST', 'TYPEID',
        'ELSE', 'IF', 'FI', 'THEN', 'NOT', 'IN', 'CASE', 'ESAC', 'CLASS',
        'INHERITS', 'ISVOID', 'LET', 'LOOP', 'NEW', 'OF',
        'POOL', 'WHILE', 'STR_CONST', 'LE', 'DARROW', 'ASSIGN', 'SPACE'
    }
    ignore = '\t '
    literals = {
        '+', '-', '*', '/', '(', ')',
        '<', '=', '.', ',', ';', ':',
        '@', '{', '}', '~'
        }
    ELSE = r'\b[eE][lL][sS][eE]\b'

    @_(r'\b[t][r][u][e]\b|\b[f][a][l][s][e]\b')
    def BOOL_CONST(self, t):
        if t.value.lower() == 'true':
            t.value = True
        else:            
            t.value = False
        return t
    
    @_(r'\b[a-z][A-Z0-9_a-z]*\b')
    def OBJECTID(self, t):
        palabras_reservadas = {'else', 'if', 'fi', 'then', 'not', 'in', 'case', 'esac', 'class', 'inherits', 'isvoid', 'let', 'loop', 'new', 'of', 'pool', 'while', 'true', 'false'}
        if t.value.lower() in palabras_reservadas:
            t.type = t.value.upper()
        return t
    
    @_(r'\b\d+\b')
    def INT_CONST(self, t):
        return t
    
    
    @_(r'[<][=]')
    def LE(self, t):
        return t
    
    @_(r'[<][-]')
    def ASSIGN(self, t):
        return t
    
    @_(r'[=][>]')
    def DARROW(self, t):
        return t
    
    @_(r'\s+')
    def SPACE(self, t):
        return t

    @_(r'\b[A-Z][A-Z0-9_a-z]*\b')
    def STR_CONST(self, t):
        if t.value == '\b':
            t.value = '\\b'
        if t.value == '\t':
            t.value = '\\t'
        if t.value == '\n':
            t.value = '\\n'
        if t.value == '\r':
            t.value = '\\r'
        return t

    @_(r'\n')
    def LINEBREAK(self, t):
        self.lineno += 1
    
    @_(r'\b[wW][hH][iI][lL][eE]\b')
    def WHILE(self, t):
        t.value = (t.value) + 'dddd'
        return t
    @_(r'.')
    def ERROR(self, t):
        print(t)
        if t.value in self.literals:
            t.type = t.value
    
    @_(r'\w+')
    def TYPEID(self, t):
        return t

    def error(self, t): #type: ignore[error]
        self.index += 1
    
    
    CARACTERES_CONTROL = [bytes.fromhex(i+hex(j)[-1]).decode('ascii')
                          for i in ['0', '1']
                          for j in range(16)] + [bytes.fromhex(hex(127)[-2:]).decode("ascii")]
    @_(r'\(\*')
    def IR(self, t):
        self.begin(Comentario)

    def error(self, t):
        self.index += 1
        
    def salida(self, texto):
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
