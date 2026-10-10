#!/usr/bin/env python3
# clike.py - the other dialects of PyTon: C, C++, C#, Java, JavaScript (NinuxOS v3.0.33).
#
#   python pyton/c2asm.py     prog.c    [-o prog.asm] [--target win64|ninux] [--name NAME]
#   python pyton/c++2asm.py   prog.cpp      python pyton/c#2asm.py  prog.cs
#   python pyton/java2asm.py  Prog.java     python pyton/js2asm.py  prog.js
#   python pyton/clike.py --show prog.c     only show the PyTon it is turned into
#
# A dialect is a way of writing, nothing more: the text is turned into PyTon and compiled by
# py2asm, so `2 + 2` written in any of them gives the very assembly py2asm gives. None of the
# language's own machinery is there - not its runtime, not its libraries.
#
# What may be written, in each of them the way that language writes it:
#   values and names (the types written in C, C#, Java are read - they decide only whether
#   `/` between whole numbers divides whole, and whether `+` joins texts); arithmetic,
#   comparisons, && || !, ?:, ++ -- += and the like; if / else, while, do-while, for, break,
#   continue, return; functions; arrays (they are lists); texts; printing in the language's own
#   way (printf, cout <<, Console.WriteLine, System.out.println, console.log).
#   The system's functions (fill, text, window, poll ...) are called by the same names.
# What is refused, as py2asm refuses `class`: classes with things of their own, struct, interface,
#   template, inheritance, new of a class, this. In C# and Java the one class that the language
#   demands around `main` is read as a wrapper and nothing else.

import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

DIALECTS = {'c': 'c', 'h': 'c', 'cpp': 'cpp', 'cc': 'cpp', 'cxx': 'cpp', 'cs': 'cs', 'java': 'java', 'js': 'js'}
TYPES = {'int', 'long', 'short', 'char', 'float', 'double', 'void', 'bool', 'boolean', 'unsigned', 'signed',
         'string', 'String', 'var', 'let', 'const', 'auto', 'size_t', 'byte', 'uint', 'ulong', 'decimal', 'object'}
MODIFIERS = {'static', 'public', 'private', 'protected', 'final', 'extern', 'inline', 'const', 'unsigned', 'signed',
             'readonly', 'internal', 'volatile', 'register', 'async', 'export'}
REFUSED = {'struct': 'a struct', 'interface': 'an interface', 'template': 'a template', 'this': '`this`',
           'extends': 'inheritance', 'implements': 'inheritance', 'virtual': 'virtual functions',
           'operator': 'operators of a class', 'union': 'a union', 'enum': 'an enum (write the numbers as names)',
           'typedef': 'typedef', 'goto': 'goto', 'switch': 'switch (write if / else if)', 'try': 'try / catch',
           'throw': 'throw', 'lambda': 'lambda'}
TOKEN = re.compile(r'''
    (?P<ws>\s+|//[^\n]*|/\*.*?\*/)
  | (?P<pre>\#[^\n]*)
  | (?P<num>0[xX][0-9a-fA-F]+|\d+\.\d*(?:[eE][-+]?\d+)?[fFdD]?|\.\d+[fF]?|\d+[uUlLfF]*)
  | (?P<istr>\$"(?:[^"\\]|\\.)*")
  | (?P<str>"(?:[^"\\]|\\.)*")
  | (?P<chr>'(?:[^'\\]|\\.)*')
  | (?P<tpl>`(?:[^`\\]|\\.)*`)
  | (?P<id>[A-Za-z_$][A-Za-z_0-9$]*)
  | (?P<op><<=|>>=|===|!==|\+\+|--|&&|\|\||==|!=|<=|>=|\+=|-=|\*=|/=|%=|&=|\|=|\^=|<<|>>|->|::|=>|[-+*/%<>=!&|^~?:;,.(){}\[\]])
''', re.S | re.X)


class DialectError(Exception):
    pass


class Translator:
    def __init__(self, text, dialect, name):
        self.d = dialect
        self.name = name
        self.toks = []
        line = 1
        pos = 0
        while pos < len(text):
            m = TOKEN.match(text, pos)
            if not m:
                raise DialectError('line %d: cannot read %r' % (line, text[pos:pos + 12]))
            kind = m.lastgroup
            if kind not in ('ws', 'pre'):
                self.toks.append((kind, m.group(), line))
            line += m.group().count('\n')
            pos = m.end()
        self.toks.append(('end', '', line))
        self.i = 0
        self.out = []
        self.types = {}             # a name -> 'int', 'float', 'str' (what its declaration said)
        self.funcs = {}             # a function -> what it gives back
        self.steps = []             # the step of each `for` we are in (continue has to do it)
        self.main = None

    # ---- tokens
    def peek(self, k=0):
        return self.toks[min(self.i + k, len(self.toks) - 1)]

    def at(self, value, k=0):
        return self.peek(k)[1] == value and self.peek(k)[0] in ('op', 'id')

    def take(self, value=None):
        t = self.peek()
        if value is not None and t[1] != value:
            self.fail('expected %s, found %s' % (value, t[1] or 'the end'))
        self.i += 1
        return t

    def fail(self, what):
        raise DialectError('%s: line %d: %s' % (self.name, self.peek()[2], what))

    def emit(self, depth, text):
        self.out.append('    ' * depth + text)

    # ---- types
    def kind_of(self, words):
        w = set(words)
        if w & {'float', 'double', 'decimal'}:
            return 'float'
        if w & {'string', 'String'} or ('char' in w and '*' in w):
            return 'str'
        if w & {'int', 'long', 'short', 'size_t', 'byte', 'uint', 'ulong', 'unsigned', 'bool', 'boolean', 'char'}:
            return 'int'
        return None

    def is_type_start(self):
        """does a declaration start here: type words, then a name"""
        k = 0
        seen = False
        while True:
            kind, v, _ = self.peek(k)
            if kind == 'id' and (v in TYPES or v in MODIFIERS):
                seen = True
                k += 1
            elif seen and v in ('*', '&'):
                k += 1
            elif seen and v == '[' and self.peek(k + 1)[1] == ']':
                k += 2
            elif seen and v == '<':             # List<int> and the like are not read
                return False
            else:
                break
        return seen and self.peek(k)[0] == 'id'

    def type_words(self):
        words = []
        while True:
            kind, v, _ = self.peek()
            if kind == 'id' and (v in TYPES or v in MODIFIERS):
                words.append(v)
                self.i += 1
            elif words and v in ('*', '&'):
                words.append('*')
                self.i += 1
            elif words and v == '[' and self.peek(1)[1] == ']':
                words.append('[]')
                self.i += 2
            else:
                return words

    # ---- expressions: each gives (PyTon text, kind)
    def expr(self):
        return self.ternary()

    def ternary(self):
        c, ck = self.binary(0)
        if self.at('?'):
            self.take()
            a, ak = self.expr()
            self.take(':')
            b, bk = self.ternary()
            return '(%s if %s else %s)' % (a, c, b), ak or bk
        return c, ck

    LEVELS = [['||'], ['&&'], ['|'], ['^'], ['&'], ['==', '!=', '===', '!=='], ['<', '>', '<=', '>='],
              ['<<', '>>'], ['+', '-'], ['*', '/', '%']]

    def binary(self, level):
        if level == len(self.LEVELS):
            return self.unary()
        a, ak = self.binary(level + 1)
        while self.peek()[0] == 'op' and self.peek()[1] in self.LEVELS[level]:
            op = self.take()[1]
            b, bk = self.binary(level + 1)
            if op == '||':
                a, ak = '(%s or %s)' % (a, b), 'int'
            elif op == '&&':
                a, ak = '(%s and %s)' % (a, b), 'int'
            elif op in ('==', '!=', '===', '!==', '<', '>', '<=', '>='):
                a, ak = '(%s %s %s)' % (a, op[:2], b), 'int'
            elif op == '+' and 'str' in (ak, bk):   # a text and something: joined, as these languages do
                if ak != 'str':
                    a = 'str(%s)' % a
                if bk != 'str':
                    b = 'str(%s)' % b
                a, ak = '(%s + %s)' % (a, b), 'str'
            elif op == '/':
                if self.d != 'js' and ak == 'int' and bk == 'int':
                    a = '(%s // %s)' % (a, b)        # whole numbers divide whole there
                else:
                    a, ak = '(%s / %s)' % (a, b), 'float'
            else:
                a = '(%s %s %s)' % (a, op, b)
                ak = 'float' if 'float' in (ak, bk) else (ak if ak == bk else (ak or bk))
        return a, ak

    def unary(self):
        kind, v, _ = self.peek()
        if kind == 'op' and v == '!':
            self.take()
            a, _ = self.unary()
            return '(not %s)' % a, 'int'
        if kind == 'op' and v in ('-', '+', '~'):
            self.take()
            a, ak = self.unary()
            return '(%s%s)' % (v, a), ak
        if kind == 'op' and v == '(' and self.peek(1)[0] == 'id' and self.peek(1)[1] in TYPES and self.peek(2)[1] == ')':
            self.take()                             # a cast: (int) x, (double) x
            t = self.take()[1]
            self.take(')')
            a, ak = self.unary()
            if t in ('float', 'double'):
                return 'float(%s)' % a, 'float'
            if t in ('int', 'long', 'short', 'char', 'byte'):
                return 'int(%s)' % a, 'int'
            return a, ak
        return self.postfix()

    def args(self):
        out = []
        self.take('(')
        while not self.at(')'):
            out.append(self.expr())
            if self.at(','):
                self.take()
        self.take(')')
        return out

    def text_with_holes(self, body, opener):
        """`a ${x} b` or $"a {x} b": the pieces of text and the values in the holes, joined.
        What stands in a hole is read by the rules of the dialect, like everything else."""
        parts = []
        pos = 0
        for m in re.finditer(re.escape(opener) + r'([^{}]*)\}', body):
            if m.start() > pos:
                parts.append('"%s"' % body[pos:m.start()].replace('"', '\\"'))
            inner = Translator(m.group(1), self.d, self.name)
            inner.types = self.types
            inner.funcs = self.funcs
            parts.append('str(%s)' % inner.expr()[0])
            pos = m.end()
        if pos < len(body):
            parts.append('"%s"' % body[pos:].replace('"', '\\"'))
        return '(%s)' % ' + '.join(parts) if parts else '""'

    def postfix(self):
        kind, v, line = self.take()
        if kind == 'num':
            v = v.rstrip('uUlL')
            if v[:2] not in ('0x', '0X') and v[-1] in 'fFdD':
                v = v[:-1]
            isfloat = '.' in v or (('e' in v or 'E' in v) and v[:2] not in ('0x', '0X'))
            a, ak = v, ('float' if isfloat else 'int')
        elif kind == 'str':
            a, ak = v, 'str'
        elif kind == 'chr':
            if self.d == 'js':
                a, ak = '"%s"' % v[1:-1].replace('"', '\\"'), 'str'
            else:
                a, ak = 'ord(%s)' % v if len(v) > 2 else '0', 'int'    # a letter is its number in C
        elif kind == 'tpl':
            a, ak = self.text_with_holes(v[1:-1], '${'), 'str'
        elif kind == 'istr':
            a, ak = self.text_with_holes(v[2:-1], '{'), 'str'
        elif kind == 'op' and v == '(':
            a, ak = self.expr()
            self.take(')')
            a = '(%s)' % a
        elif kind == 'op' and v == '{':             # {1, 2, 3}: an array written out
            items = []
            while not self.at('}'):
                items.append(self.expr()[0])
                if self.at(','):
                    self.take()
            self.take('}')
            a, ak = '[%s]' % ', '.join(items), None
        elif kind == 'op' and v == '[':             # [1, 2, 3] in JavaScript
            items = []
            while not self.at(']'):
                items.append(self.expr()[0])
                if self.at(','):
                    self.take()
            self.take(']')
            a, ak = '[%s]' % ', '.join(items), None
        elif kind == 'op' and v in ('++', '--'):
            self.fail('++ and -- stand on a line of their own here (x++;), not inside an expression')
        elif kind == 'id':
            if v in REFUSED:
                self.fail('%s is not part of the dialect: plain code only, no machinery of classes' % REFUSED[v])
            if v == 'new':
                if self.peek()[1] in TYPES and self.peek(1)[1] == '[':
                    self.take()                     # new int[n]: a list of n zeros
                    self.take('[')
                    if self.at(']'):
                        self.take(']')
                        return self.postfix()
                    n = self.expr()[0]
                    self.take(']')
                    return '[0 for _ in range(%s)]' % n, None
                self.fail('`new` of a class is not part of the dialect (arrays: new int[n])')
            if v in ('true', 'false'):
                return ('True' if v == 'true' else 'False'), 'int'
            if v in ('null', 'NULL', 'nullptr', 'undefined'):
                return 'None', None
            a, ak = v, self.types.get(v)
        else:
            self.fail('an expression cannot start with %s' % (v or 'the end'))
        while True:
            if self.at('('):
                ar = self.args()
                ak = self.funcs.get(a)
                a = '%s(%s)' % (a, ', '.join(x[0] for x in ar))
            elif self.at('['):
                self.take()
                ix = self.expr()[0]
                self.take(']')
                a = '%s[%s]' % (a, ix)
                ak = 'int' if ak != 'str' else 'str'
            elif self.at('.') or self.at('::') or self.at('->'):
                self.take()
                member = self.take()[1]
                if member in ('length', 'Length', 'size', 'Count') :
                    if self.at('('):
                        self.args()
                    a, ak = 'len(%s)' % a, 'int'
                elif a == 'Math' or a == 'std':
                    a = {'floor': 'int', 'abs': 'abs', 'max': 'max', 'min': 'min', 'Abs': 'abs', 'Max': 'max',
                         'Min': 'min', 'Floor': 'int'}.get(member, member)
                else:
                    a = '%s.%s' % (a, member)
            else:
                return a, ak

    # ---- printing, the way each language writes it
    def printf(self, ar):
        if not ar:
            return 'print()'
        fmt = ar[0][0]
        rest = [x[0] for x in ar[1:]]
        if not (fmt.startswith('"') and fmt.endswith('"')):
            return 'print(%s, end="")' % fmt
        body = fmt[1:-1]
        newline = body.endswith('\\n')
        if newline:
            body = body[:-2]
        parts = []
        pos = 0
        for m in re.finditer(r'%(?:[-+ 0#]*\d*(?:\.\d+)?)(?:l|ll|h|z)?([disfcxXu%g])', body):
            if m.start() > pos:
                parts.append('"%s"' % body[pos:m.start()])
            c = m.group(1)
            if c == '%':
                parts.append('"%"')
            else:
                if not rest:
                    self.fail('printf: more %% places than values')
                v = rest.pop(0)
                parts.append({'c': 'chr(%s)' % v, 'x': 'hex(%s)[2:]' % v, 'X': 'hex(%s)[2:].upper()' % v}.get(c, 'str(%s)' % v))
            pos = m.end()
        if pos < len(body):
            parts.append('"%s"' % body[pos:])
        text = ' + '.join(parts) if parts else '""'
        return 'print(%s)' % text if newline else 'print(%s, end="")' % text

    def print_call(self, line_kind, ar):
        vals = [x[0] for x in ar]
        if line_kind == 'line':
            return 'print(%s)' % ', '.join(vals)
        return 'print(%s, end="")' % (', '.join(vals) if vals else '""')

    # ---- statements
    def simple(self, depth):
        """a statement without its ';' (also the parts of a for)"""
        if self.is_type_start():
            words = self.type_words()
            kind = self.kind_of(words)
            while True:
                name = self.take()[1]
                arr = None
                if self.at('['):                    # int a[10]
                    self.take()
                    arr = self.expr()[0] if not self.at(']') else ''
                    self.take(']')
                if '[]' in words or arr is not None:
                    self.types[name] = None
                else:
                    self.types[name] = kind
                if self.at('='):
                    self.take()
                    v, vk = self.expr()
                    if kind is None and '[]' not in words and arr is None:
                        self.types[name] = vk       # var / let / auto: what it is given says what it is
                    if kind == 'float' and vk == 'int':
                        v = 'float(%s)' % v
                    self.emit(depth, '%s = %s' % (name, v))
                elif arr:
                    self.emit(depth, '%s = [0 for _ in range(%s)]' % (name, arr))
                else:
                    self.emit(depth, '%s = %s' % (name, {'float': '0.0', 'str': '""'}.get(kind, '0')))
                if self.at(','):
                    self.take()
                    continue
                return
        # printing
        t = self.peek()
        if t[0] == 'id':
            if t[1] == 'printf' and self.peek(1)[1] == '(':
                self.take()
                self.emit(depth, self.printf(self.args()))
                return
            if t[1] == 'puts' and self.peek(1)[1] == '(':
                self.take()
                self.emit(depth, 'print(%s)' % self.args()[0][0])
                return
            if t[1] in ('cout', 'std') and self.d == 'cpp':
                self.take()
                if self.at('::'):
                    self.take()
                    self.take('cout')
                vals = []
                newline = False
                while self.at('<<'):
                    self.take()
                    if self.at('endl') or (self.at('std') and self.peek(2)[1] == 'endl'):
                        if self.at('std'):
                            self.take()
                            self.take()
                        self.take()
                        newline = True
                    else:
                        v = self.binary(8)[0]
                        if v.endswith('\\n"'):
                            v = v[:-3] + '"'
                            newline = True
                        vals.append('str(%s)' % v)
                text = ' + '.join(vals) if vals else '""'
                self.emit(depth, 'print(%s)' % text if newline else 'print(%s, end="")' % text)
                return
            chain = [self.peek(k)[1] for k in range(6)]
            for words, kind in ((['Console', '.', 'WriteLine'], 'line'), (['Console', '.', 'Write'], 'part'),
                                (['System', '.', 'out', '.', 'println'], 'line'), (['System', '.', 'out', '.', 'print'], 'part'),
                                (['console', '.', 'log'], 'line')):
                if chain[:len(words)] == words and chain[len(words)] == '(':
                    self.i += len(words)
                    self.emit(depth, self.print_call(kind, self.args()))
                    return
        if self.at('++') or self.at('--'):
            op = self.take()[1]
            target = self.postfix()[0]
            self.emit(depth, '%s %s= 1' % (target, op[0]))
            return
        target, tk = self.expr()
        if self.at('++') or self.at('--'):
            op = self.take()[1]
            self.emit(depth, '%s %s= 1' % (target, op[0]))
        elif self.peek()[0] == 'op' and self.peek()[1] in ('=', '+=', '-=', '*=', '/=', '%=', '&=', '|=', '^=', '<<=', '>>='):
            op = self.take()[1]
            v, vk = self.expr()
            if target.startswith('(') and target.endswith(')'):
                target = target[1:-1]
            if op == '/=' and self.d != 'js' and tk == 'int' and vk == 'int':
                op = '//='
            if op == '+=' and tk == 'str' and vk != 'str':
                v = 'str(%s)' % v
            self.emit(depth, '%s %s %s' % (target, op, v))
        else:
            self.emit(depth, target)

    def block(self, depth):
        """{ ... } or one statement; an empty one is `pass`"""
        before = len(self.out)
        if self.at('{'):
            self.take()
            while not self.at('}'):
                self.statement(depth)
            self.take('}')
        else:
            self.statement(depth)
        if len(self.out) == before:
            self.emit(depth, 'pass')

    def statement(self, depth):
        t = self.peek()
        v = t[1]
        if t[0] == 'op' and v == ';':
            self.take()
        elif t[0] == 'op' and v == '{':
            self.block(depth)
        elif t[0] == 'id' and v in REFUSED:
            self.fail('%s is not part of the dialect: plain code only, no machinery of classes' % REFUSED[v])
        elif t[0] == 'id' and v == 'if':
            self.take()
            self.take('(')
            c = self.expr()[0]
            self.take(')')
            self.emit(depth, 'if %s:' % c)
            self.block(depth + 1)
            while self.at('else'):
                self.take()
                if self.at('if'):
                    self.take()
                    self.take('(')
                    c = self.expr()[0]
                    self.take(')')
                    self.emit(depth, 'elif %s:' % c)
                    self.block(depth + 1)
                else:
                    self.emit(depth, 'else:')
                    self.block(depth + 1)
                    break
        elif t[0] == 'id' and v == 'while':
            self.take()
            self.take('(')
            c = self.expr()[0]
            self.take(')')
            self.emit(depth, 'while %s:' % c)
            self.steps.append(None)
            self.block(depth + 1)
            self.steps.pop()
        elif t[0] == 'id' and v == 'do':
            self.take()
            self.emit(depth, 'while True:')
            self.steps.append(None)
            self.block(depth + 1)
            self.steps.pop()
            self.take('while')
            self.take('(')
            c = self.expr()[0]
            self.take(')')
            self.emit(depth + 1, 'if not %s:' % c)
            self.emit(depth + 2, 'break')
        elif t[0] == 'id' and v == 'for':
            self.take()
            self.take('(')
            if not self.at(';'):
                self.simple(depth)
            self.take(';')
            c = 'True' if self.at(';') else self.expr()[0]
            self.take(';')
            step = []
            if not self.at(')'):
                keep = self.out
                self.out = step
                self.simple(0)
                while self.at(','):
                    self.take()
                    self.simple(0)
                self.out = keep
            self.take(')')
            self.emit(depth, 'while %s:' % c)
            self.steps.append(step)
            self.block(depth + 1)
            self.steps.pop()
            for line in step:
                self.emit(depth + 1, line)
        elif t[0] == 'id' and v == 'return':
            self.take()
            if self.at(';'):
                self.emit(depth, 'return')
            else:
                self.emit(depth, 'return %s' % self.expr()[0])
        elif t[0] == 'id' and v == 'break':
            self.take()
            self.emit(depth, 'break')
        elif t[0] == 'id' and v == 'continue':
            self.take()
            if self.steps and self.steps[-1]:
                for line in self.steps[-1]:         # the step of the for is done before going round
                    self.emit(depth, line)
            self.emit(depth, 'continue')
        else:
            self.simple(depth)
            if self.at(';'):
                self.take()

    # ---- the top: functions, things kept outside them, the wrappers a language demands
    def function_here(self):
        """is a function written here: [words] name ( ... ) {"""
        k = 0
        if self.at('function'):
            return True
        while self.peek(k)[0] == 'id' and (self.peek(k)[1] in TYPES or self.peek(k)[1] in MODIFIERS):
            k += 1
        while self.peek(k)[1] in ('*', '&', '[', ']'):
            k += 1
        if k == 0 or self.peek(k)[0] != 'id' or self.peek(k + 1)[1] != '(':
            return False
        depth = 0
        j = k + 1
        while True:
            v = self.peek(j)[1]
            if v == '(':
                depth += 1
            elif v == ')':
                depth -= 1
                if depth == 0:
                    return self.peek(j + 1)[1] == '{'
            elif v == '' or v == ';':
                return False
            j += 1

    def function(self, depth):
        if self.at('function'):
            self.take()
            words = []
        else:
            words = self.type_words()
        name = self.take()[1]
        self.funcs[name] = self.kind_of(words)
        outer = self.types
        self.types = dict(outer)
        params = []
        self.take('(')
        while not self.at(')'):
            pw = self.type_words()
            if self.at(')'):                        # f(void)
                break
            p = self.take()[1]
            if self.at('['):
                self.take()
                self.take(']')
                pw.append('[]')
            self.types[p] = None if '[]' in pw else self.kind_of(pw)
            params.append(p)
            if self.at(','):
                self.take()
        self.take(')')
        if name in ('main', 'Main'):
            self.main = name
            params = []                             # what the system would hand it is not there
        globals_here = [g for g in outer if g not in params]
        self.emit(depth, 'def %s(%s):' % (name, ', '.join(params)))
        start = len(self.out)
        self.block(depth + 1)
        body = self.out[start:]
        assigned = set()
        for line in body:
            m = re.match(r'\s*([A-Za-z_]\w*)\s*(?:=|\+=|-=|\*=|/=|//=|%=)[^=]', line)
            if m:
                assigned.add(m.group(1))
        declared = set(self.types) - set(outer)
        names = sorted(g for g in globals_here if g in assigned and g not in declared and g in self.top)
        if names:
            self.out.insert(start, '    ' * (depth + 1) + 'global ' + ', '.join(names))
        self.types = outer

    def translate(self):
        self.top = set()
        while self.peek()[0] != 'end':
            t = self.peek()
            if t[0] == 'id' and t[1] in ('using', 'import', 'package'):
                while not self.at(';'):
                    self.take()
                self.take()
            elif t[0] == 'id' and t[1] == 'namespace':
                self.take()
                while not self.at('{') and not self.at(';'):
                    self.take()
                self.take()                         # its braces are read as a wrapper
                self.wrappers = getattr(self, 'wrappers', 0) + 1
            elif t[0] == 'id' and (t[1] == 'class' or (t[1] in MODIFIERS and self.peek(1)[1] == 'class')
                                   or (t[1] in MODIFIERS and self.peek(2)[1] == 'class')):
                if self.d not in ('cs', 'java'):
                    self.fail('a class is not part of the dialect: plain code only')
                while not self.at('class'):
                    self.take()
                self.take()
                self.take()                         # its name
                if not self.at('{'):
                    self.fail('inheritance is not part of the dialect')
                self.take()
                self.wrappers = getattr(self, 'wrappers', 0) + 1
            elif t[0] == 'op' and t[1] == '}' and getattr(self, 'wrappers', 0) > 0:
                self.take()
                self.wrappers -= 1
            elif self.function_here():
                self.function(0)
            else:
                before = set(self.types)
                self.statement(0)
                self.top |= set(self.types) - before
        if self.main and self.d != 'js':            # C, C++, C#, Java start at main; JavaScript at its first line
            self.emit(0, '%s()' % self.main)
        return '\n'.join(self.out) + '\n'


def translate(text, dialect, name='the program'):
    return Translator(text, dialect, name).translate()


def main(dialect=None):
    args = sys.argv[1:]
    show = '--show' in args
    args = [a for a in args if a != '--show']
    if not args:
        sys.exit(__doc__)
    src = args[0]
    d = dialect or DIALECTS.get(src.rsplit('.', 1)[-1].lower())
    if not d:
        sys.exit('clike: which dialect is %s? (.c .cpp .cs .java .js)' % src)
    try:
        py = translate(open(src, encoding='utf-8-sig').read(), d, os.path.basename(src))
    except DialectError as e:
        sys.exit('%s2asm: %s' % (d, e))
    if show:
        print(py, end='')
        return 0
    mid = os.path.splitext(src)[0] + '.pyton.py'
    with open(mid, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# made from %s by pyton/clike.py (%s) - change the program, not this file\n' % (os.path.basename(src), d) + py)
    rest = args[1:]
    if '-o' not in rest and '--out' not in rest:
        rest += ['-o', os.path.splitext(src)[0] + '.asm']
    r = subprocess.run([sys.executable, os.path.join(HERE, 'py2asm.py'), mid] + rest)
    return r.returncode


if __name__ == '__main__':
    sys.exit(main())
