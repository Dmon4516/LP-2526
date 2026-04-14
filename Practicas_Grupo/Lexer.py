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


class CoolLexer(Lexer):
    tokens = {
        'OBJECTID', 'INT_CONST', 'BOOL_CONST', 'TYPEID',
        'ELSE', 'IF', 'FI', 'THEN', 'NOT', 'IN', 'CASE', 'ESAC', 'CLASS',
        'INHERITS', 'ISVOID', 'LET', 'LOOP', 'NEW', 'OF',
        'POOL', 'WHILE', 'STR_CONST', 'LE', 'DARROW', 'ASSIGN'
    }

    ignore = ' \t\x0b\x0c'

    literals = {
        '+', '-', '*', '/', '(', ')', '<',
        '.', ',', ';', ':', '@', '{', '}', '~', '='
    }

    LE     = r'<='
    DARROW = r'=>'
    ASSIGN = r'<-'

    @_(r'[0-9]+')
    def INT_CONST(self, t):
        t.value = str(t.value)
        return t

    @_(r'"')
    def STR_CONST(self, t):
        string_value = ''
        error_msg = None
        i = self.index
        text = self.text
        length = len(text)

        while i < length:
            c = text[i]

            if c == '\x00':
                error_msg = 'String contains null character.'
                i += 1
                while i < length and text[i] != '"' and text[i] != '\n':
                    i += 1
                if i < length and text[i] == '"':
                    i += 1
                break

            elif c == '\\':
                i += 1
                if i >= length:
                    error_msg = 'EOF in string constant'
                    break
                nc = text[i]
                if nc == '\x00':
                    error_msg = 'String contains escaped null character.'
                    i += 1
                    while i < length and text[i] != '"' and text[i] != '\n':
                        i += 1
                    if i < length and text[i] == '"':
                        i += 1
                    break
                elif nc == 'n':
                    string_value += '\n'
                elif nc == 't':
                    string_value += '\t'
                elif nc == 'b':
                    string_value += '\b'
                elif nc == 'f':
                    string_value += '\f'
                elif nc == '\\':
                    string_value += '\\'
                elif nc == '"':
                    string_value += '"'
                elif nc == '\n':
                    self.lineno += 1
                    string_value += '\n'
                else:
                    string_value += nc
                i += 1

            elif c == '"':
                i += 1
                break

            elif c == '\n':
                error_msg = 'Unterminated string constant'
                self.lineno += 1
                i += 1
                break

            else:
                string_value += c
                i += 1

        else:
            if error_msg is None:
                error_msg = 'EOF in string constant'

        self.index = i

        if error_msg:
            t.type = 'ERROR'
            t.value = error_msg
            return t

        if len(string_value) > 1024:
            t.type = 'ERROR'
            t.value = 'String constant too long'
            return t

        t.value = string_value
        return t

    @_(r'--[^\n]*')
    def COMENTARIO_LINEA(self, t):
        pass

    @_(r'\(\*')
    def COMENTARIO_MULTI(self, t):
        nivel = 1
        i = self.index
        text = self.text
        length = len(text)

        while i < length and nivel > 0:
            c = text[i]
            if c == '"':
                i += 1
                while i < length:
                    cc = text[i]
                    if cc == '\\':
                        i += 2 
                    elif cc == '"':
                        i += 1
                        break
                    elif cc == '\n':
                        self.lineno += 1
                        i += 1
                    else:
                        i += 1
            elif c == '(' and i + 1 < length and text[i + 1] == '*':
                nivel += 1
                i += 2
            elif c == '*' and i + 1 < length and text[i + 1] == ')':
                nivel -= 1
                i += 2
            elif c == '\n':
                self.lineno += 1
                i += 1
            else:
                i += 1

        if nivel > 0:
            t.type = 'ERROR'
            t.value = 'EOF in comment'
            self.index = i
            return t

        self.index = i

    @_(r'\*\)')
    def COMENTARIO_CIERRE(self, t):
        t.type = 'ERROR'
        t.value = 'Unmatched *)'
        return t

    @_(r'\n')
    def NEWLINE(self, t):
        self.lineno += 1

    @_(r'\r')
    def CR(self, t):
        pass

    @_(r'[a-zA-Z][a-zA-Z0-9_]*')
    def IDENTIFIER(self, t):
        val_lower = t.value.lower()

        if t.value[0].islower() and val_lower == 'true':
            t.type = 'BOOL_CONST'
            t.value = True
            return t
        if t.value[0].islower() and val_lower == 'false':
            t.type = 'BOOL_CONST'
            t.value = False
            return t

        keywords = {
            'class': 'CLASS', 'else': 'ELSE', 'fi': 'FI',
            'if': 'IF', 'in': 'IN', 'inherits': 'INHERITS',
            'isvoid': 'ISVOID', 'let': 'LET', 'loop': 'LOOP',
            'pool': 'POOL', 'then': 'THEN', 'while': 'WHILE',
            'case': 'CASE', 'esac': 'ESAC', 'new': 'NEW',
            'of': 'OF', 'not': 'NOT',
        }
        if val_lower in keywords:
            t.type = keywords[val_lower]
            return t

        if t.value[0].isupper():
            t.type = 'TYPEID'
            return t

        t.type = 'OBJECTID'
        return t

    CARACTERES_CONTROL = [
        bytes.fromhex(i + hex(j)[-1]).decode('ascii')
        for i in ['0', '1']
        for j in range(16)
    ] + [bytes.fromhex(hex(127)[-2:]).decode("ascii")]

    def error(self, t):
        char = t.value[0]
        code = ord(char)
        if code < 32 or code == 127:
            error_val = f'\\{code:03o}'
        elif char == '\\':
            error_val = '\\\\'
        else:
            error_val = char
        t.type = 'ERROR'
        t.value = error_val
        self.index += 1
        return t

    def _str_para_salida(self, s):
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

    def salida(self, texto):
        lexer = CoolLexer()
        list_strings = []
        for token in lexer.tokenize(texto):
            if token.type == 'OBJECTID':
                result = f'#{token.lineno} {token.type} {token.value}'
            elif token.type == 'BOOL_CONST':
                val = 'true' if token.value else 'false'
                result = f'#{token.lineno} {token.type} {val}'
            elif token.type == 'TYPEID':
                result = f'#{token.lineno} {token.type} {token.value}'
            elif token.type in self.literals:
                result = f'#{token.lineno} \'{token.type}\' '
            elif token.type == 'STR_CONST':
                escaped = self._str_para_salida(token.value)
                result = f'#{token.lineno} {token.type} "{escaped}"'
            elif token.type == 'INT_CONST':
                result = f'#{token.lineno} {token.type} {token.value}'
            elif token.type == 'ERROR':
                result = f'#{token.lineno} {token.type} "{token.value}"'
            else:
                result = f'#{token.lineno} {token.type}'
            list_strings.append(result)
        return list_strings

