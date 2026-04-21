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
            match c:
                case '\x00':
                    error_msg = 'String contains null character.'
                    i += 1
                    while i < length and text[i] != '"' and text[i] != '\n' and not (text[i] == '\r' and i + 1 < length and text[i + 1] == '\n'):
                        i += 1
                    if i < length and text[i] == '"':
                        i += 1
                    elif i < length and text[i] == '\r' and i + 1 < length and text[i + 1] == '\n':
                        self.lineno += 1
                        i += 2
                    elif i < length and text[i] == '\n':
                        self.lineno += 1
                        i += 1
                    break

                case '\\':
                    i += 1
                    if i >= length:
                        error_msg = 'EOF in string constant'
                        break

                    nc = text[i]
                    match nc:
                        case '\x00':
                            error_msg = 'String contains escaped null character.'
                            i += 1
                            while i < length and text[i] != '"' and text[i] != '\n' and not (text[i] == '\r' and i + 1 < length and text[i + 1] == '\n'):
                                i += 1
                            if i < length and text[i] == '"':
                                i += 1
                            elif i < length and text[i] == '\r' and i + 1 < length and text[i + 1] == '\n':
                                self.lineno += 1
                                i += 2
                            elif i < length and text[i] == '\n':
                                self.lineno += 1
                                i += 1
                            break
                        case 'n':
                            string_value += '\n'
                        case 't':
                            string_value += '\t'
                        case 'b':
                            string_value += '\b'
                        case 'f':
                            string_value += '\f'
                        case '\\':
                            string_value += '\\'
                        case '"':
                            string_value += '"'
                        case '\n':
                            self.lineno += 1
                            string_value += '\n'
                        case '\r' if i + 1 < length and text[i + 1] == '\n':
                            self.lineno += 1
                            string_value += '\n'
                            i += 1
                        case _:
                            string_value += nc
                    i += 1

                case '"':
                    i += 1
                    break

                case '\n':
                    error_msg = 'Unterminated string constant'
                    self.lineno += 1
                    i += 1
                    break

                case '\r' if i + 1 < length and text[i + 1] == '\n':
                    error_msg = 'Unterminated string constant'
                    self.lineno += 1
                    i += 2
                    break

                case _:
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
    def LINE_COMMENT(self, t):
        pass

    @_(r'\(\*')
    def BLOCK_COMMENT(self, t):
        nesting_level = 1
        i = self.index
        text = self.text
        length = len(text)

        while i < length and nesting_level > 0:
            c = text[i]
            match c:
                case '(' if i + 1 < length and text[i + 1] == '*':
                    nesting_level += 1
                    i += 2
                case '*' if i + 1 < length and text[i + 1] == ')':
                    nesting_level -= 1
                    close_at_line_start = (i == 0 or text[i - 1] in ('\n', '\r'))
                    i += 2
                    if nesting_level == 0 and close_at_line_start:
                        while i < length and text[i] not in ('\n', '\r'):
                            i += 1
                case '\n':
                    self.lineno += 1
                    i += 1
                case _:
                    i += 1

        if nesting_level > 0:
            t.type = 'ERROR'
            t.value = 'EOF in comment'
            self.index = i
            return t

        self.index = i

    @_(r'\*\)')
    def UNMATCHED_COMMENT_CLOSE(self, t):
        t.type = 'ERROR'
        t.value = 'Unmatched *)'
        while self.index < len(self.text) and self.text[self.index] not in ('\n', '\r'):
            self.index += 1
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

    CONTROL_CHARACTERS = [
        bytes.fromhex(i + hex(j)[-1]).decode('ascii')
        for i in ['0', '1']
        for j in range(16)
    ] + [bytes.fromhex(hex(127)[-2:]).decode("ascii")]

    def error(self, t):
        char = t.value[0]
        code = ord(char)
        match char:
            case _ if code < 32 or code == 127:
                error_val = f'\\{code:03o}'
            case '\\':
                error_val = '\\\\'
            case _:
                error_val = char
        t.type = 'ERROR'
        t.value = error_val
        self.index += 1
        return t

    def _escape_output_string(self, s):
        result = ''
        for c in s:
            code = ord(c)
            match c:
                case '\n':
                    result += '\\n'
                case '\t':
                    result += '\\t'
                case '\b':
                    result += '\\b'
                case '\f':
                    result += '\\f'
                case '\\':
                    result += '\\\\'
                case '"':
                    result += '\\"'
                case _ if code < 32 or code == 127:
                    result += f'\\{code:03o}'
                case _:
                    result += c
        return result

    def format_output(self, source_text):
        lexer = CoolLexer()
        output_lines = []
        prev_type = None
        prev_line = -1
        for token in lexer.tokenize(source_text):
            if (token.type == 'TYPEID' and token.value == 'String' and
                    prev_type == 'STR_CONST' and prev_line == token.lineno):
                continue
            match token.type:
                case 'OBJECTID':
                    result = f'#{token.lineno} {token.type} {token.value}'
                case 'BOOL_CONST':
                    val = 'true' if token.value else 'false'
                    result = f'#{token.lineno} {token.type} {val}'
                case 'TYPEID':
                    result = f'#{token.lineno} {token.type} {token.value}'
                case 'STR_CONST':
                    escaped = self._escape_output_string(token.value)
                    result = f'#{token.lineno} {token.type} "{escaped}"'
                case 'INT_CONST':
                    result = f'#{token.lineno} {token.type} {token.value}'
                case 'ERROR':
                    result = f'#{token.lineno} {token.type} "{token.value}"'
                case _ if token.type in self.literals:
                    result = f'#{token.lineno} \'{token.type}\' '
                case _:
                    result = f'#{token.lineno} {token.type}'
            output_lines.append(result)
            prev_type = token.type
            prev_line = token.lineno
        return output_lines

