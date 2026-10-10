#!/usr/bin/env python3
# py2asm.py - PyTon to x86-64 assembly (NinuxOS v2.9.60; written anew, the old one was lost).
#
#   python pyton/py2asm.py prog.py                       -> prog.asm, a Windows program (to try the language)
#        nasm -f win64 -I pyton/ prog.asm -o prog.obj    gcc prog.obj -o prog.exe
#   python pyton/py2asm.py prog.py --target ninux --name NAME
#        nasm -f bin -I pyton/ prog.asm -o NAME.asmo     -> an ASMO v4 object (see platform_ninux.inc)
#
# The program is read with Python's own parser, so the syntax is exactly Python's. What is compiled:
#   numbers (whole and fractions), texts, True False None, lists, tuples, dicts
#   + - * / // % ** & | ^ << >> ~, comparisons (also a < b < c), and or not, in, is, x if c else y
#   = with several names and with a, b = ..., += and the like, del, assert
#   if elif else, while, for (range, texts, lists, tuples, dicts) with break, continue and else
#   def with default values and name=value in the call, return, global
#   s[i], s[-1], s[a:b:c], f"...{x:>8.2f}...", [x for x in ... if ...]
#   print len str int float bool repr chr ord abs min max sum any all sorted reversed enumerate
#   zip range list tuple dict divmod round pow input
#   the methods of texts, lists and dicts that prelude.py has (_m_NAME)
# Not yet: class, import, try / except, with, lambda, yield, nested def, *args, sets.
# Whole numbers are 63 bits; memory is not given back.

import argparse
import ast
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


class CompileError(Exception):
    pass


def fail(node, text):
    raise CompileError('line %d: %s' % (getattr(node, 'lineno', 0), text))


# name in prelude.py -> (the label in runtime.inc, how many values it takes)
INTRINSICS = {
    '_type': ('i_type', 1), '_str_new': ('i_str_new', 1), '_sget': ('i_sget', 2), '_sset': ('i_sset', 3),
    '_list_new': ('i_list_new', 1), '_push': ('rt_list_push', 2), '_lget': ('i_lget', 2),
    '_lset': ('i_lset', 3), '_lsetlen': ('i_lsetlen', 2), '_settype': ('i_settype', 2),
    '_dkeys': ('i_dkeys', 1), '_dvals': ('i_dvals', 1), '_bval': ('i_bval', 1),
    '_fadd': ('i_fadd', 2), '_fsub': ('i_fsub', 2), '_fmul': ('i_fmul', 2), '_fdiv': ('i_fdiv', 2),
    '_fsqrt': ('i_fsqrt', 1), '_flt': ('i_flt', 2), '_feq': ('i_feq', 2), '_i2f': ('i_i2f', 1),
    '_f2i': ('i_f2i', 1), '_write': ('i_write', 1), '_readline': ('i_readline', 0),
    '_error': ('i_error', 1), '_exit': ('i_exit', 1),
}
REGS = ['rdi', 'rsi', 'rdx', 'rcx']

# a built-in function of Python -> the function of prelude.py that does it
BUILTINS = {
    'str': '_str', 'repr': '_repr', 'int': '_int', 'float': '_float', 'bool': '_bool', 'chr': '_chr',
    'ord': '_ord', 'abs': '_abs', 'sum': '_sum', 'any': '_any', 'all': '_all', 'sorted': '_sorted',
    'reversed': '_reversed', 'enumerate': '_enumerate', 'zip': '_zip', 'divmod': '_divmod',
    'round': '_round', 'list': '_list', 'tuple': '_tuple', 'dict': '_dict', 'input': '_input',
}

BINOPS = {ast.Add: 'rt_add', ast.Sub: 'rt_sub', ast.Mult: 'rt_mul', ast.Div: 'rt_div',
          ast.FloorDiv: 'rt_floordiv', ast.Mod: 'rt_mod', ast.Pow: 'rt_pow', ast.BitAnd: 'rt_and',
          ast.BitOr: 'rt_or', ast.BitXor: 'rt_xor', ast.LShift: 'rt_shl', ast.RShift: 'rt_shr'}
CMPOPS = {ast.Eq: 'rt_eq', ast.NotEq: 'rt_ne', ast.Lt: 'rt_lt', ast.LtE: 'rt_le', ast.Gt: 'rt_gt',
          ast.GtE: 'rt_ge', ast.In: 'rt_in', ast.NotIn: 'rt_notin', ast.Is: 'rt_is', ast.IsNot: 'rt_isnot'}

# the functions of prelude.py that runtime.inc calls by itself
RUNTIME_NEEDS = ['_add', '_sub', '_mul', '_truediv', '_floordiv', '_mod', '_pow', '_neg', '_eq', '_lt',
                 '_le', '_contains', '_dict_get', '_dict_set']

NOT_YET = {ast.ClassDef: 'class', ast.Import: 'import', ast.ImportFrom: 'import', ast.Try: 'try / except',
           ast.With: 'with', ast.Lambda: 'lambda', ast.Yield: 'yield', ast.YieldFrom: 'yield',
           ast.AsyncFunctionDef: 'async', ast.Await: 'await', ast.Set: 'a set { }', ast.SetComp: 'a set { }',
           ast.DictComp: 'a dict made with for', ast.GeneratorExp: 'a generator ( ... for ... )',
           ast.Starred: '*name', ast.Nonlocal: 'nonlocal', ast.NamedExpr: ':='}


def stores(body):
    """the names given a value in these statements (not looking into def)"""
    found = []

    def walk(node):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            return
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            if node.id not in found:
                found.append(node.id)
        for child in ast.iter_child_nodes(node):
            walk(child)
    for st in body:
        walk(st)
    return found


def declared_global(body):
    names = set()
    for st in body:
        for node in ast.walk(st):
            if isinstance(node, ast.Global):
                names.update(node.names)
    return names


class Function:
    def __init__(self, name, node, body, is_main, prelude):
        self.name, self.node, self.body, self.is_main, self.prelude = name, node, body, is_main, prelude
        self.label = 'f_' + name
        self.params = []
        self.defaults = {}
        if node is not None:
            a = node.args
            if a.vararg or a.kwarg or a.kwonlyargs or a.posonlyargs:
                fail(node, 'def %s: *args, **kwargs and the like are not compiled yet' % name)
            self.params = [p.arg for p in a.args]
            for p, d in zip(self.params[len(self.params) - len(a.defaults):], a.defaults):
                self.defaults[p] = d
        self.globals = set() if is_main else declared_global(body)
        self.locals = [] if is_main else [n for n in stores(body)
                                          if n not in self.globals and n not in self.params]
        self.slots = {}
        self.nslots = 0

    def slot(self, name=None):
        if name is not None and name in self.slots:
            return self.slots[name]
        self.nslots += 1
        off = '[rbp - %d]' % (8 * self.nslots)
        if name is not None:
            self.slots[name] = off
        return off


class Compiler:
    def __init__(self, target, encoding):
        self.target, self.encoding = target, encoding
        self.funcs = {}
        self.out = []
        self.texts = {}
        self.floats = {}
        self.nlabel = 0
        self.done = set()
        self.queue = []
        self.globals = []
        self.fn = None
        self.loops = []
        self.meta = {}

    # ------------------------------------------------------------ small things
    def emit(self, line):
        self.out.append('        ' + line)

    def label(self, name):
        self.out.append(name + ':')

    def new_label(self):
        self.nlabel += 1
        return 'L%d' % self.nlabel

    def need(self, name):
        if name not in self.done and name not in self.queue:
            self.queue.append(name)
        return self.funcs[name].label

    def text(self, s):
        if s not in self.texts:
            self.texts[s] = 'c_s%d' % len(self.texts)
        return self.texts[s]

    def const(self, node, value):
        if value is None:
            self.emit('lea rax, [rel rt_none]')
        elif value is True:
            self.emit('lea rax, [rel rt_true]')
        elif value is False:
            self.emit('lea rax, [rel rt_false]')
        elif isinstance(value, int):
            if not -2 ** 62 <= value < 2 ** 62:
                fail(node, 'the number %d is too big (whole numbers are 63 bits)' % value)
            self.emit('mov rax, %d' % (value * 2 + 1))
        elif isinstance(value, float):
            if value not in self.floats:
                self.floats[value] = 'c_f%d' % len(self.floats)
            self.emit('lea rax, [rel %s]' % self.floats[value])
        elif isinstance(value, str):
            self.emit('lea rax, [rel %s]' % self.text(value))
        else:
            fail(node, 'a value of this kind cannot be written in a program: %r' % (value,))

    # ------------------------------------------------------------ names
    def place(self, node, name, storing):
        fn = self.fn
        if not fn.is_main:
            if name in fn.params:
                return '[rbp + %d]' % (16 + 8 * (len(fn.params) - 1 - fn.params.index(name)))
            if name in fn.locals:
                return fn.slot(name)
        if name in self.globals and not fn.prelude:
            return '[rel g_%s]' % name
        if storing:
            fail(node, 'the name %s cannot be given a value here' % name)
        fail(node, 'the name %s is used but never given a value' % name)

    def call_function(self, node, name, args, keywords):
        f = self.funcs[name]
        shown = name[3:] if name.startswith('_m_') else name
        if len(args) > len(f.params):
            fail(node, '%s() takes %d values, %d were given' % (shown, len(f.params), len(args)))
        given = dict(zip(f.params, args))
        for k in keywords:
            if k.arg is None:
                fail(node, '**name in a call is not compiled yet')
            if k.arg not in f.params:
                fail(node, '%s() has no value called %s' % (shown, k.arg))
            if k.arg in given:
                fail(node, '%s() gets %s twice' % (shown, k.arg))
            given[k.arg] = k.value
        for p in f.params:
            if p in given:
                self.expr(given[p])
            elif p in f.defaults:
                self.expr(f.defaults[p])
            else:
                fail(node, '%s() needs a value for %s' % (shown, p))
            self.emit('push rax')
        self.emit('call %s' % self.need(name))
        if f.params:
            self.emit('add rsp, %d' % (8 * len(f.params)))

    def call_runtime(self, label, args):
        for a in args:
            self.expr(a)
            self.emit('push rax')
        for i in reversed(range(len(args))):
            self.emit('pop %s' % REGS[i])
        self.emit('call %s' % label)

    # ------------------------------------------------------------ expressions: the value comes in rax
    def expr(self, node):
        kind = type(node)
        if kind in NOT_YET:
            fail(node, '%s is not compiled yet' % NOT_YET[kind])
        m = getattr(self, 'e_' + kind.__name__, None)
        if m is None:
            fail(node, 'this is not compiled yet (%s)' % kind.__name__)
        m(node)

    def e_Constant(self, node):
        self.const(node, node.value)

    def e_Name(self, node):
        self.emit('mov rax, %s' % self.place(node, node.id, False))

    def e_BinOp(self, node):
        self.call_runtime(BINOPS[type(node.op)], [node.left, node.right])

    def e_UnaryOp(self, node):
        if isinstance(node.op, ast.USub) and isinstance(node.operand, ast.Constant) \
                and isinstance(node.operand.value, (int, float)) and not isinstance(node.operand.value, bool):
            self.const(node, -node.operand.value)
            return
        self.expr(node.operand)
        if isinstance(node.op, ast.UAdd):
            return
        self.emit('mov rdi, rax')
        self.emit('call %s' % {ast.USub: 'rt_neg', ast.Not: 'rt_not', ast.Invert: 'rt_invert'}[type(node.op)])

    def e_BoolOp(self, node):
        end = self.new_label()
        for i, v in enumerate(node.values):
            self.expr(v)
            if i < len(node.values) - 1:
                self.emit('push rax')
                self.emit('mov rdi, rax')
                self.emit('call rt_truth')
                self.emit('test eax, eax')
                self.emit('pop rax')
                self.emit('%s %s' % ('jz' if isinstance(node.op, ast.And) else 'jnz', end))
        self.label(end)

    def e_Compare(self, node):
        if len(node.ops) == 1:
            self.call_runtime(CMPOPS[type(node.ops[0])], [node.left, node.comparators[0]])
            return
        end = self.new_label()
        left = self.fn.slot()
        right = self.fn.slot()
        self.expr(node.left)
        self.emit('mov %s, rax' % left)
        for i, (op, c) in enumerate(zip(node.ops, node.comparators)):
            self.expr(c)
            self.emit('mov %s, rax' % right)
            self.emit('mov rdi, %s' % left)
            self.emit('mov rsi, rax')
            self.emit('call %s' % CMPOPS[type(op)])
            if i < len(node.ops) - 1:
                self.emit('lea rcx, [rel rt_false]')
                self.emit('cmp rax, rcx')
                self.emit('je %s' % end)
                self.emit('mov rcx, %s' % right)
                self.emit('mov %s, rcx' % left)
        self.label(end)

    def e_IfExp(self, node):
        other, end = self.new_label(), self.new_label()
        self.jump_if_false(node.test, other)
        self.expr(node.body)
        self.emit('jmp %s' % end)
        self.label(other)
        self.expr(node.orelse)
        self.label(end)

    def sequence(self, node, kind):
        self.emit('mov edi, %d' % len(node.elts))
        self.emit('call rt_list_new')
        self.emit('push rax')
        for e in node.elts:
            self.expr(e)
            self.emit('mov rsi, rax')
            self.emit('mov rdi, [rsp]')
            self.emit('call rt_list_push')
        self.emit('pop rax')
        if kind == 5:
            self.emit('mov qword [rax], 5')

    def e_List(self, node):
        self.sequence(node, 2)

    def e_Tuple(self, node):
        self.sequence(node, 5)

    def e_Dict(self, node):
        self.emit('call rt_dict_new')
        self.emit('push rax')
        for k, v in zip(node.keys, node.values):
            if k is None:
                fail(node, '**name inside { } is not compiled yet')
            self.expr(k)
            self.emit('push rax')
            self.expr(v)
            self.emit('mov rdx, rax')
            self.emit('pop rsi')
            self.emit('mov rdi, [rsp]')
            self.emit('call rt_setitem')
        self.emit('pop rax')

    def e_Subscript(self, node):
        if isinstance(node.slice, ast.Slice):
            s = node.slice
            none = ast.Constant(value=None)
            self.call_function(node, '_slice', [node.value, s.lower or none, s.upper or none, s.step or none], [])
        else:
            self.call_runtime('rt_getitem', [node.value, node.slice])

    def e_JoinedStr(self, node):
        first = True
        if not node.values:
            self.const(node, '')
            return
        for v in node.values:
            if not first:
                self.emit('push rax')
            if isinstance(v, ast.Constant):
                self.const(v, v.value)
            else:
                spec = ast.Constant(value=None)
                if v.format_spec is not None:
                    parts = v.format_spec.values
                    if len(parts) != 1 or not isinstance(parts[0], ast.Constant):
                        fail(node, 'a { } inside the format of an f-string is not compiled yet')
                    spec = parts[0]
                if v.conversion == 114:
                    self.call_function(node, '_repr', [v.value], [])
                else:
                    self.call_function(node, '_fmt', [v.value, spec], [])
            if not first:
                self.emit('mov rsi, rax')
                self.emit('pop rdi')
                self.emit('call rt_add')
            first = False

    def e_ListComp(self, node):
        name = '_comp%d' % self.nlabel
        self.nlabel += 1
        if self.fn.is_main:
            if name not in self.globals:
                self.globals.append(name)
        else:
            self.fn.locals.append(name)
        target = ast.Name(id=name, ctx=ast.Store())
        body = [ast.Expr(value=ast.Call(func=ast.Attribute(value=ast.Name(id=name, ctx=ast.Load()),
                                                           attr='append', ctx=ast.Load()),
                                        args=[node.elt], keywords=[]))]
        for gen in reversed(node.generators):
            if gen.is_async:
                fail(node, 'async is not compiled')
            for cond in reversed(gen.ifs):
                body = [ast.If(test=cond, body=body, orelse=[])]
            body = [ast.For(target=gen.target, iter=gen.iter, body=body, orelse=[])]
        block = [ast.Assign(targets=[target], value=ast.List(elts=[], ctx=ast.Load()))] + body
        for st in block:
            ast.copy_location(st, node)
            ast.fix_missing_locations(st)
            self.stmt(st)
        self.emit('mov rax, %s' % self.place(node, name, False))

    def e_Call(self, node):
        f = node.func
        if isinstance(f, ast.Attribute):
            name = '_m_' + f.attr
            if name not in self.funcs:
                fail(node, 'the method .%s() is not there yet' % f.attr)
            self.call_function(node, name, [f.value] + node.args, node.keywords)
            return
        if not isinstance(f, ast.Name):
            fail(node, 'only a function called by its name is compiled')
        name = f.id
        if any(isinstance(a, ast.Starred) for a in node.args):
            fail(node, '*name in a call is not compiled yet')
        if name in self.funcs and (self.fn.prelude or not self.funcs[name].prelude):
            self.call_function(node, name, node.args, node.keywords)
        elif name in INTRINSICS and self.fn.prelude:
            label, count = INTRINSICS[name]
            if len(node.args) != count:
                fail(node, '%s takes %d values' % (name, count))
            self.call_runtime(label, node.args)
        elif name == 'print':
            sep, end = ast.Constant(value=' '), ast.Constant(value='\n')
            for k in node.keywords:
                if k.arg == 'sep':
                    sep = k.value
                elif k.arg == 'end':
                    end = k.value
                else:
                    fail(node, 'print() knows only sep= and end=')
            self.call_function(node, '_print', [ast.List(elts=node.args, ctx=ast.Load()), sep, end], [])
        elif name == 'len':
            if len(node.args) != 1:
                fail(node, 'len() takes one value')
            self.call_runtime('rt_len', node.args)
        elif name == 'pow':
            if len(node.args) != 2:
                fail(node, 'pow() takes two values here')
            self.call_runtime('rt_pow', node.args)
        elif name in ('min', 'max'):
            if not node.args:
                fail(node, '%s() of nothing' % name)
            arg = node.args[0] if len(node.args) == 1 else ast.List(elts=node.args, ctx=ast.Load())
            self.call_function(node, '_' + name, [arg], [])
        elif name == 'range':
            self.call_function(node, '_range_list', self.range_args(node), [])
        elif name in BUILTINS:
            self.call_function(node, BUILTINS[name], node.args, node.keywords)
        else:
            fail(node, 'the function %s() is not defined' % name)

    def range_args(self, node):
        a = node.args
        if node.keywords or not 1 <= len(a) <= 3:
            fail(node, 'range() takes one, two or three numbers')
        if len(a) == 1:
            return [ast.Constant(value=0), a[0], ast.Constant(value=1)]
        if len(a) == 2:
            return [a[0], a[1], ast.Constant(value=1)]
        return list(a)

    def jump_if_false(self, test, label):
        self.expr(test)
        self.emit('mov rdi, rax')
        self.emit('call rt_truth')
        self.emit('test eax, eax')
        self.emit('jz %s' % label)

    # ------------------------------------------------------------ statements
    def store(self, target):
        """rax goes into target"""
        if isinstance(target, ast.Name):
            self.emit('mov %s, rax' % self.place(target, target.id, True))
        elif isinstance(target, ast.Subscript):
            if isinstance(target.slice, ast.Slice):
                fail(target, 's[a:b] = ... is not compiled yet')
            self.emit('push rax')
            self.expr(target.value)
            self.emit('push rax')
            self.expr(target.slice)
            self.emit('mov rsi, rax')
            self.emit('pop rdi')
            self.emit('pop rdx')
            self.emit('call rt_setitem')
        elif isinstance(target, (ast.Tuple, ast.List)):
            tmp = self.fn.slot()
            self.emit('mov %s, rax' % tmp)
            for i, t in enumerate(target.elts):
                if isinstance(t, ast.Starred):
                    fail(target, '*name on the left of = is not compiled yet')
                self.emit('mov rdi, %s' % tmp)
                self.emit('mov rsi, %d' % (i * 2 + 1))
                self.emit('call rt_getitem')
                self.store(t)
        else:
            fail(target, 'this cannot be given a value (objects with .name are not compiled yet)')

    def stmt(self, node):
        kind = type(node)
        if kind in NOT_YET:
            fail(node, '%s is not compiled yet' % NOT_YET[kind])
        m = getattr(self, 's_' + kind.__name__, None)
        if m is None:
            fail(node, 'this is not compiled yet (%s)' % kind.__name__)
        m(node)

    def block(self, body):
        for st in body:
            self.stmt(st)

    def s_Expr(self, node):
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return                              # a text alone on a line: a comment
        self.expr(node.value)

    def s_Pass(self, node):
        pass

    def s_Global(self, node):
        pass

    def s_FunctionDef(self, node):
        fail(node, 'def inside a def is not compiled yet - put it at the top of the program')

    def s_Assign(self, node):
        self.expr(node.value)
        if len(node.targets) == 1:
            self.store(node.targets[0])
            return
        tmp = self.fn.slot()
        self.emit('mov %s, rax' % tmp)
        for t in node.targets:
            self.emit('mov rax, %s' % tmp)
            self.store(t)

    def s_AnnAssign(self, node):
        if node.value is not None:
            self.expr(node.value)
            self.store(node.target)

    def s_AugAssign(self, node):
        op = BINOPS[type(node.op)]
        t = node.target
        if isinstance(t, ast.Name):
            self.emit('mov rax, %s' % self.place(t, t.id, False))
            self.emit('push rax')
            self.expr(node.value)
            self.emit('mov rsi, rax')
            self.emit('pop rdi')
            self.emit('call %s' % op)
            self.emit('mov %s, rax' % self.place(t, t.id, True))
        elif isinstance(t, ast.Subscript) and not isinstance(t.slice, ast.Slice):
            obj, key = self.fn.slot(), self.fn.slot()
            self.expr(t.value)
            self.emit('mov %s, rax' % obj)
            self.expr(t.slice)
            self.emit('mov %s, rax' % key)
            self.emit('mov rdi, %s' % obj)
            self.emit('mov rsi, rax')
            self.emit('call rt_getitem')
            self.emit('push rax')
            self.expr(node.value)
            self.emit('mov rsi, rax')
            self.emit('pop rdi')
            self.emit('call %s' % op)
            self.emit('mov rdx, rax')
            self.emit('mov rdi, %s' % obj)
            self.emit('mov rsi, %s' % key)
            self.emit('call rt_setitem')
        else:
            fail(node, 'this cannot be changed with an operator and =')

    def s_Delete(self, node):
        for t in node.targets:
            if isinstance(t, ast.Subscript) and not isinstance(t.slice, ast.Slice):
                self.call_function(node, '_delitem', [t.value, t.slice], [])
            elif isinstance(t, ast.Name):
                self.emit('lea rax, [rel rt_none]')
                self.store(t)
            else:
                fail(node, 'del of this is not compiled yet')

    def s_Assert(self, node):
        ok = self.new_label()
        self.expr(node.test)
        self.emit('mov rdi, rax')
        self.emit('call rt_truth')
        self.emit('test eax, eax')
        self.emit('jnz %s' % ok)
        self.call_function(node, '_assert_fail', [node.msg or ast.Constant(value='line %d' % node.lineno)], [])
        self.label(ok)

    def s_Raise(self, node):
        msg = ast.Constant(value='raise')
        if isinstance(node.exc, ast.Call) and node.exc.args:
            msg = node.exc.args[0]
        elif isinstance(node.exc, ast.Name):
            msg = ast.Constant(value=node.exc.id)
        self.call_function(node, '_assert_fail', [msg], [])

    def s_If(self, node):
        other, end = self.new_label(), self.new_label()
        self.jump_if_false(node.test, other)
        self.block(node.body)
        if node.orelse:
            self.emit('jmp %s' % end)
        self.label(other)
        self.block(node.orelse)
        self.label(end)

    def s_While(self, node):
        top, other, end = self.new_label(), self.new_label(), self.new_label()
        self.label(top)
        self.jump_if_false(node.test, other)
        self.loops.append((top, end))
        self.block(node.body)
        self.loops.pop()
        self.emit('jmp %s' % top)
        self.label(other)
        self.block(node.orelse)
        self.label(end)

    def s_For(self, node):
        top, cont, other, end = self.new_label(), self.new_label(), self.new_label(), self.new_label()
        it = node.iter
        step = None
        if isinstance(it, ast.Call) and isinstance(it.func, ast.Name) and it.func.id == 'range' \
                and 'range' not in self.funcs:
            args = self.range_args(it)
            s = args[2]
            if isinstance(s, ast.UnaryOp) and isinstance(s.op, ast.USub) and isinstance(s.operand, ast.Constant):
                s = ast.Constant(value=-s.operand.value)
            if isinstance(s, ast.Constant) and isinstance(s.value, int) and s.value != 0 \
                    and abs(s.value) < 2 ** 30:
                step = s.value
        if step is not None:                    # for i in range(...): a plain counter
            count, stop = self.fn.slot(), self.fn.slot()
            self.expr(args[0])
            self.emit('mov %s, rax' % count)
            self.expr(args[1])
            self.emit('mov %s, rax' % stop)
            self.label(top)
            self.emit('mov rax, %s' % count)
            self.emit('cmp rax, %s' % stop)
            self.emit('%s %s' % ('jge' if step > 0 else 'jle', other))
            self.store(node.target)
            self.loops.append((cont, end))
            self.block(node.body)
            self.loops.pop()
            self.label(cont)
            self.emit('add qword %s, %d' % (count, 2 * step))
            self.emit('jmp %s' % top)
        else:                                   # over a text, a list, a tuple, the keys of a dict
            seq, index = self.fn.slot(), self.fn.slot()
            self.call_function(node, '_iter', [it], [])
            self.emit('mov %s, rax' % seq)
            self.emit('mov qword %s, 1' % index)
            self.label(top)
            self.emit('mov rdi, %s' % seq)
            self.emit('call rt_len')
            self.emit('cmp %s, rax' % index)
            self.emit('jge %s' % other)
            self.emit('mov rdi, %s' % seq)
            self.emit('mov rsi, %s' % index)
            self.emit('call rt_getitem')
            self.store(node.target)
            self.loops.append((cont, end))
            self.block(node.body)
            self.loops.pop()
            self.label(cont)
            self.emit('add qword %s, 2' % index)
            self.emit('jmp %s' % top)
        self.label(other)
        self.block(node.orelse)
        self.label(end)

    def s_Break(self, node):
        if not self.loops:
            fail(node, 'break outside a loop')
        self.emit('jmp %s' % self.loops[-1][1])

    def s_Continue(self, node):
        if not self.loops:
            fail(node, 'continue outside a loop')
        self.emit('jmp %s' % self.loops[-1][0])

    def s_Return(self, node):
        if self.fn.is_main:
            fail(node, 'return outside a function')
        if node.value is None:
            self.emit('lea rax, [rel rt_none]')
        else:
            self.expr(node.value)
        self.emit('jmp e_%s' % self.fn.name)

    # ------------------------------------------------------------ a whole function, a whole program
    def function(self, fn):
        self.fn = fn
        self.loops = []
        head = self.out
        self.out = []
        if fn.is_main:
            for g in self.globals:
                self.emit('lea rax, [rel rt_none]')
                self.emit('mov [rel g_%s], rax' % g)
        self.block(fn.body)
        body = self.out
        self.out = head
        self.out.append('')
        self.label(fn.label)
        self.emit('push rbp')
        self.emit('mov rbp, rsp')
        if fn.nslots:
            self.emit('sub rsp, %d' % ((8 * fn.nslots + 15) & ~15))
        named = sorted(fn.slots.values())
        if named:
            self.emit('lea rax, [rel rt_none]')
            for off in named:
                self.emit('mov %s, rax' % off)
        self.out.extend(body)
        self.emit('lea rax, [rel rt_none]')
        self.label('e_' + fn.name)
        self.emit('mov rsp, rbp')
        self.emit('pop rbp')
        self.emit('ret')
        self.fn = None

    def add_source(self, source, filename, prelude):
        tree = ast.parse(source, filename)
        rest = []
        for st in tree.body:
            if isinstance(st, ast.FunctionDef):
                if st.name in self.funcs:
                    fail(st, 'the function %s is defined twice' % st.name)
                if not prelude and st.name in INTRINSICS:
                    fail(st, 'the name %s is taken by the system' % st.name)
                self.funcs[st.name] = Function(st.name, st, st.body, False, prelude)
            else:
                rest.append(st)
        return rest

    def compile(self, source, filename):
        prelude = open(os.path.join(HERE, 'prelude.py'), encoding='utf-8').read()
        self.add_source(prelude, 'prelude.py', True)
        user = [n for n in self.funcs]
        main_body = self.add_source(source, filename, False)
        user = [n for n in self.funcs if n not in user]
        for st in main_body:                    # META = {...} at the top describes the object
            if isinstance(st, ast.Assign) and len(st.targets) == 1 and isinstance(st.targets[0], ast.Name) \
                    and st.targets[0].id == 'META':
                try:
                    self.meta = dict(ast.literal_eval(st.value))
                except ValueError:
                    fail(st, 'META must be a plain dict of texts')
        self.globals = stores(main_body)
        for name in user:
            for g in sorted(self.funcs[name].globals):
                if g not in self.globals:
                    self.globals.append(g)
        self.funcs['__main__'] = Function('__main__', None, main_body, True, False)
        self.user = user
        self.queue = ['__main__'] + user + RUNTIME_NEEDS
        while self.queue:
            name = self.queue.pop(0)
            if name in self.done:
                continue
            self.done.add(name)
            self.function(self.funcs[name])
        return self.assembly(filename)

    def data(self):
        lines = ['', 'RT_DATA', '        align 8']
        for g in self.globals:
            lines.append('g_%s: dq 0' % g)
        for value, label in self.floats.items():
            lines.append('%s: dq 4, 0x%016X' % (label, struct.unpack('<Q', struct.pack('<d', value))[0]))
        for s, label in self.texts.items():
            raw = s.encode(self.encoding, errors='replace')
            lines.append('        align 8')
            lines.append('%s: dq 1, %d' % (label, len(raw)))
            for i in range(0, len(raw), 16):
                lines.append('        db ' + ', '.join(str(b) for b in raw[i:i + 16]))
            lines.append('        db 0')
        lines.append('RT_TEXT')
        return lines

    def assembly(self, filename):
        head = ['; made by py2asm.py from %s - do not change this file, change the program' % os.path.basename(filename),
                'bits 64', 'default rel']
        if self.target == 'win64':
            head += ['%include "platform_win64.inc"', '%include "runtime.inc"']
            return '\n'.join(head + self.out + self.data()) + '\n'
        return '\n'.join(head + self.ninux_object()) + '\n'

    def ninux_object(self):
        """the program as one ASMO v4 object: header, META, the socket tables, the code, the end"""
        meta = {'type': 'app'}
        meta.update({str(k): str(v) for k, v in self.meta.items()})
        meta.setdefault('name', self.object_name)
        sockets = [s.strip() for s in meta.get('sockets', '').split(',') if s.strip()]
        if not sockets:
            sockets = [n for n in self.user if not n.startswith('_')]
        for s in sockets:
            if s not in self.user:
                raise CompileError('META names the socket %s but there is no def %s' % (s, s))
            if len(self.funcs[s].params) > 2:
                raise CompileError('a socket takes at most two values: def %s' % s)
        meta['sockets'] = ','.join(sockets)
        meta.setdefault('lang', 'pyton')
        meta['made'] = 'py2asm (v2.9.60)'
        o = ['org 0', '%include "platform_ninux.inc"', 'obj_start:',
             "        db 'OMSA'", '        dd 4', '        dq obj_end - obj_start',
             '        dq obj_data - obj_start', '        dq obj_meta - obj_start',
             '        dq obj_system - obj_start', '        dq obj_named - obj_start',
             '        dq obj_prockets - obj_start', '        dq 1', '        dq 0',
             '        dd 1', '        dd 0                    ; the identity: the system must give it (TODO.md)',
             '        dq 0', '        dq obj_meta - obj_data', '        dq 0                    ; no relocations: the code is position-independent',
             'obj_data:', 'obj_meta:']
        for k, v in meta.items():
            raw = ('%s:%s' % (k, v)).encode(self.encoding, errors='replace')
            o.append('        db ' + ', '.join(str(b) for b in raw) + ', 0')
        o += ['        db 0', 'obj_system:', '        times 9 dq obj_stub - obj_start', '        dq 0',
              'obj_stub:', '        ret', 'obj_named:']
        o += ['        dq sock_%s - obj_start' % s for s in sockets]
        o += ['        dq 0', 'obj_prockets:', '        dq 0, 0']
        for s in sockets:
            n = len(self.funcs[s].params)
            o += ['', 'sock_%s:' % s, '        NINUX_SOCKET_ENTER']
            if n >= 1:
                o += ['        lea rax, [rdx*2 + 1]', '        push rax']
            if n == 2:
                o += ['        lea rax, [rcx*2 + 1]', '        push rax']
            o += ['        call f_%s' % s]
            if n:
                o += ['        add rsp, %d' % (8 * n)]
            o += ['        jmp ninux_socket_leave']
        o += ['', 'NINUX_PLATFORM_CODE', '%include "runtime.inc"'] + self.out + self.data()
        o += ['        times (8 - ($ - $$) % 8) % 8 db 0x90', '        dq obj_end - obj_start',
              "        db 'ASMO', 0, 0, 0, 0", 'obj_end:']
        return o


def main():
    ap = argparse.ArgumentParser(description='PyTon to x86-64 assembly')
    ap.add_argument('source')
    ap.add_argument('-o', '--out')
    ap.add_argument('--target', choices=['win64', 'ninux'], default='win64')
    ap.add_argument('--name', help='the name of the object (ninux); default: the file name')
    ap.add_argument('--encoding', help='how texts are stored; default utf-8 (win64), cp1251 (ninux)')
    a = ap.parse_args()
    c = Compiler(a.target, a.encoding or ('cp1251' if a.target == 'ninux' else 'utf-8'))
    c.object_name = a.name or os.path.splitext(os.path.basename(a.source))[0].lower()
    try:
        text = c.compile(open(a.source, encoding='utf-8-sig').read(), a.source)
    except CompileError as e:
        sys.exit('py2asm: %s: %s' % (a.source, e))
    except SyntaxError as e:
        sys.exit('py2asm: %s: line %s: %s' % (a.source, e.lineno, e.msg))
    out = a.out or os.path.splitext(a.source)[0] + '.asm'
    with open(out, 'w', newline='\n') as f:
        f.write(text)
    print('py2asm: %s -> %s (%d functions)' % (a.source, out, len(c.done)))


if __name__ == '__main__':
    main()
