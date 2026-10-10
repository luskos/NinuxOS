# prelude.py - the part of PyTon that is written in PyTon (NinuxOS v2.9.60).
#
# py2asm compiles this file together with every program and keeps only the functions the
# program needs. Here are: what + - * / do with texts, lists and fractions, comparing, str(),
# int(), print(), slices, and the methods (.append, .split, .get ...).
#
# It stands on a few functions written in assembly (pyton/runtime.inc), all with a "_" in front:
#   _type(x)  0 number, 1 text, 2 list, 3 dict, 4 float, 5 tuple, 6 None, 7 bool
#   _str_new(n) _sget(s, i) _sset(s, i, byte)        texts, byte by byte
#   _list_new(room) _push(l, v) _lget(l, i) _lset(l, i, v) _lsetlen(l, n) _settype(l, kind)
#   _dkeys(d) _dvals(d)                              the two lists inside a dict
#   _fadd _fsub _fmul _fdiv _fsqrt _flt _feq _i2f _f2i   fractions (floats)
#   _bval(b) _write(s) _readline() _error(s) _exit(n)
# Rule for this file: a + - * < == here must work on whole numbers only, or go through the
# functions above - the general cases come back to this file, and must not loop.


# ---------------------------------------------------------------- arithmetic

def _concat(a, b):
    la = len(a)
    lb = len(b)
    r = _str_new(la + lb)
    i = 0
    while i < la:
        _sset(r, i, _sget(a, i))
        i = i + 1
    i = 0
    while i < lb:
        _sset(r, la + i, _sget(b, i))
        i = i + 1
    return r


def _arith(a, b, op):
    # op: 0 +   1 -   2 *   3 /   4 //   5 %
    ta = _type(a)
    tb = _type(b)
    if ta == 7:
        a = _bval(a)
        ta = 0
    if tb == 7:
        b = _bval(b)
        tb = 0
    if ta == 0 and tb == 0:
        if op == 0:
            return a + b
        if op == 1:
            return a - b
        if op == 2:
            return a * b
        if op == 4:
            return a // b
        if op == 5:
            return a % b
        if b == 0:
            _raise("ZeroDivisionError", "division by zero")
        return _fdiv(_i2f(a), _i2f(b))
    if (ta == 0 or ta == 4) and (tb == 0 or tb == 4):
        if ta == 0:
            a = _i2f(a)
        if tb == 0:
            b = _i2f(b)
        if op == 0:
            return _fadd(a, b)
        if op == 1:
            return _fsub(a, b)
        if op == 2:
            return _fmul(a, b)
        if _feq(b, 0.0):
            _raise("ZeroDivisionError", "division by zero")
        q = _fdiv(a, b)
        if op == 3:
            return q
        f = _i2f(_f2i(q))
        if _flt(q, f):
            f = _fsub(f, 1.0)
        if op == 4:
            return f
        return _fsub(a, _fmul(f, b))
    _raise("TypeError", "these two values cannot be combined with + - * / // %")


def _repeat(seq, n):
    t = _type(seq)
    if n < 0:
        n = 0
    ln = len(seq)
    if t == 1:
        r = _str_new(ln * n)
        k = 0
        while k < n:
            i = 0
            while i < ln:
                _sset(r, k * ln + i, _sget(seq, i))
                i = i + 1
            k = k + 1
        return r
    r = _list_new(ln * n)
    k = 0
    while k < n:
        i = 0
        while i < ln:
            _push(r, _lget(seq, i))
            i = i + 1
        k = k + 1
    if t == 5:
        _settype(r, 5)
    return r


def _add(a, b):
    ta = _type(a)
    tb = _type(b)
    if ta == 1 and tb == 1:
        return _concat(a, b)
    if (ta == 2 and tb == 2) or (ta == 5 and tb == 5):
        la = len(a)
        lb = len(b)
        r = _list_new(la + lb)
        i = 0
        while i < la:
            _push(r, _lget(a, i))
            i = i + 1
        i = 0
        while i < lb:
            _push(r, _lget(b, i))
            i = i + 1
        if ta == 5:
            _settype(r, 5)
        return r
    if ta == 1 or tb == 1:
        _raise("TypeError", "a text can only be added to a text - use str()")
    return _arith(a, b, 0)


def _sub(a, b):
    if _type(a) == 9 and _type(b) == 9:
        return _m_difference(a, b)
    return _arith(a, b, 1)


def _mul(a, b):
    ta = _type(a)
    tb = _type(b)
    if (ta == 1 or ta == 2 or ta == 5) and tb == 0:
        return _repeat(a, b)
    if (tb == 1 or tb == 2 or tb == 5) and ta == 0:
        return _repeat(b, a)
    return _arith(a, b, 2)


def _truediv(a, b):
    return _arith(a, b, 3)


def _floordiv(a, b):
    return _arith(a, b, 4)


def _mod(a, b):
    return _arith(a, b, 5)


def _neg(a):
    t = _type(a)
    if t == 4:
        return _fsub(0.0, a)
    if t == 7:
        return 0 - _bval(a)
    _error("only a number can have a minus in front")


def _pow(a, b):
    tb = _type(b)
    if tb == 7:
        b = _bval(b)
        tb = 0
    if tb == 4:
        if _feq(b, 0.5):
            if _type(a) == 0:
                a = _i2f(a)
            return _fsqrt(a)
        _error("** with a fraction as the power: only 0.5 (the square root)")
    if tb != 0:
        _error("** needs numbers")
    if b < 0:
        return _arith(1, _pow(a, 0 - b), 3)
    r = 1
    while b > 0:
        if b % 2 == 1:
            r = _mul2(r, a)
        a = _mul2(a, a)
        b = b // 2
    return r


def _mul2(a, b):
    if _type(a) == 0 and _type(b) == 0:
        return a * b
    return _arith(a, b, 2)


# ---------------------------------------------------------------- comparing

def _isnum(t):
    return t == 0 or t == 4 or t == 7


def _tofloat(x):
    t = _type(x)
    if t == 0:
        return _i2f(x)
    if t == 7:
        return _i2f(_bval(x))
    return x


def _eq(a, b):
    ta = _type(a)
    tb = _type(b)
    if _isnum(ta) and _isnum(tb):
        if ta != 4 and tb != 4:
            if ta == 7:
                a = _bval(a)
            if tb == 7:
                b = _bval(b)
            return a == b
        return _feq(_tofloat(a), _tofloat(b))
    if ta != tb:
        return False
    if ta == 1:
        n = len(a)
        if n != len(b):
            return False
        i = 0
        while i < n:
            if _sget(a, i) != _sget(b, i):
                return False
            i = i + 1
        return True
    if ta == 2 or ta == 5:
        n = len(a)
        if n != len(b):
            return False
        i = 0
        while i < n:
            if _lget(a, i) != _lget(b, i):
                return False
            i = i + 1
        return True
    if ta == 9:
        n = len(a)
        if n != len(b):
            return False
        i = 0
        while i < n:
            if not _contains(b, _lget(a, i)):
                return False
            i = i + 1
        return True
    if ta == 3:
        ka = _dkeys(a)
        n = len(ka)
        if n != len(_dkeys(b)):
            return False
        i = 0
        while i < n:
            j = _dict_find(b, _lget(ka, i))
            if j < 0:
                return False
            if _lget(_dvals(a), i) != _lget(_dvals(b), j):
                return False
            i = i + 1
        return True
    return False


def _order(a, b):
    # -1 a before b, 0 the same, 1 a after b
    ta = _type(a)
    tb = _type(b)
    if _isnum(ta) and _isnum(tb):
        if ta != 4 and tb != 4:
            if ta == 7:
                a = _bval(a)
            if tb == 7:
                b = _bval(b)
            if a < b:
                return -1
            if a > b:
                return 1
            return 0
        fa = _tofloat(a)
        fb = _tofloat(b)
        if _flt(fa, fb):
            return -1
        if _flt(fb, fa):
            return 1
        return 0
    if ta == 1 and tb == 1:
        la = len(a)
        lb = len(b)
        i = 0
        while i < la and i < lb:
            ca = _sget(a, i)
            cb = _sget(b, i)
            if ca < cb:
                return -1
            if ca > cb:
                return 1
            i = i + 1
        if la < lb:
            return -1
        if la > lb:
            return 1
        return 0
    if (ta == 2 and tb == 2) or (ta == 5 and tb == 5):
        la = len(a)
        lb = len(b)
        i = 0
        while i < la and i < lb:
            c = _order(_lget(a, i), _lget(b, i))
            if c != 0:
                return c
            i = i + 1
        if la < lb:
            return -1
        if la > lb:
            return 1
        return 0
    _raise("TypeError", "these two values cannot be compared with < >")


def _lt(a, b):
    return _order(a, b) < 0


def _le(a, b):
    return _order(a, b) <= 0


def _find_text(s, sub, start):
    n = len(s)
    m = len(sub)
    i = start
    while i + m <= n:
        j = 0
        while j < m and _sget(s, i + j) == _sget(sub, j):
            j = j + 1
        if j == m:
            return i
        i = i + 1
    return -1


def _contains(c, x):
    t = _type(c)
    if t == 1:
        if _type(x) != 1:
            _error("'in' a text needs a text on the left")
        return _find_text(c, x, 0) >= 0
    if t == 2 or t == 5 or t == 9:
        n = len(c)
        i = 0
        while i < n:
            if _lget(c, i) == x:
                return True
            i = i + 1
        return False
    if t == 3:
        return _dict_find(c, x) >= 0
    _error("'in' needs a text, a list, a tuple or a dict on the right")


# ---------------------------------------------------------------- dicts

def _dict_find(d, k):
    keys = _dkeys(d)
    n = len(keys)
    i = 0
    while i < n:
        if _lget(keys, i) == k:
            return i
        i = i + 1
    return -1


def _dict_get(d, k):
    i = _dict_find(d, k)
    if i < 0:
        _raise("KeyError", _repr(k))
    return _lget(_dvals(d), i)


def _dict_set(d, k, v):
    i = _dict_find(d, k)
    if i < 0:
        _push(_dkeys(d), k)
        _push(_dvals(d), v)
    else:
        _lset(_dvals(d), i, v)
    return None


def _remove_at(l, i):
    n = len(l)
    while i < n - 1:
        _lset(l, i, _lget(l, i + 1))
        i = i + 1
    _lsetlen(l, n - 1)
    return None


def _delitem(o, k):
    t = _type(o)
    if t == 3:
        i = _dict_find(o, k)
        if i < 0:
            _raise("KeyError", _repr(k))
        _remove_at(_dkeys(o), i)
        _remove_at(_dvals(o), i)
        return None
    if t == 2:
        n = len(o)
        if k < 0:
            k = k + n
        if k < 0 or k >= n:
            _raise("IndexError", "del: the index is outside the list")
        _remove_at(o, k)
        return None
    _error("del works on a list or a dict")


# ---------------------------------------------------------------- slices: s[a:b:c]

def _slice(o, lo, hi, step):
    t = _type(o)
    n = len(o)
    if step is None:
        step = 1
    if step == 0:
        _error("a slice step cannot be 0")
    if step > 0:
        if lo is None:
            lo = 0
        if hi is None:
            hi = n
        if lo < 0:
            lo = lo + n
        if hi < 0:
            hi = hi + n
        if lo < 0:
            lo = 0
        if hi > n:
            hi = n
    else:
        if lo is None:
            lo = n - 1
        elif lo < 0:
            lo = lo + n
        if hi is None:
            hi = -1
        else:
            if hi < 0:
                hi = hi + n
            if hi < -1:
                hi = -1
        if lo >= n:
            lo = n - 1
    count = 0
    i = lo
    if step > 0:
        while i < hi:
            count = count + 1
            i = i + step
    else:
        while i > hi:
            count = count + 1
            i = i + step
    if t == 1:
        r = _str_new(count)
        i = lo
        k = 0
        while k < count:
            _sset(r, k, _sget(o, i))
            i = i + step
            k = k + 1
        return r
    if t == 2 or t == 5:
        r = _list_new(count)
        i = lo
        k = 0
        while k < count:
            _push(r, _lget(o, i))
            i = i + step
            k = k + 1
        if t == 5:
            _settype(r, 5)
        return r
    _error("only a text, a list or a tuple can be sliced")


# ---------------------------------------------------------------- to text and back

def _int_str(n):
    if n == 0:
        return "0"
    neg = 0
    if n < 0:
        neg = 1
        n = 0 - n
    digits = _list_new(20)
    while n > 0:
        _push(digits, 48 + n % 10)
        n = n // 10
    k = len(digits)
    r = _str_new(k + neg)
    if neg == 1:
        _sset(r, 0, 45)
    i = 0
    while i < k:
        _sset(r, neg + i, _lget(digits, k - 1 - i))
        i = i + 1
    return r


def _float_str(f):
    # up to 6 digits after the point, the zeros at the end taken off (Python shows up to 17)
    sign = ""
    if _flt(f, 0.0):
        sign = "-"
        f = _fsub(0.0, f)
    whole = _f2i(f)
    frac = _f2i(_fadd(_fmul(_fsub(f, _i2f(whole)), 1000000.0), 0.5))
    if frac >= 1000000:
        whole = whole + 1
        frac = frac - 1000000
    d = _int_str(frac)
    while len(d) < 6:
        d = _concat("0", d)
    k = 6
    while k > 1 and _sget(d, k - 1) == 48:
        k = k - 1
    return _concat(_concat(sign, _int_str(whole)), _concat(".", _slice(d, 0, k, 1)))


def _str(x):
    t = _type(x)
    if t == 1:
        return x
    if t == 0:
        return _int_str(x)
    if t == 4:
        return _float_str(x)
    if t == 6:
        return "None"
    if t == 7:
        if x:
            return "True"
        return "False"
    return _repr(x)


def _repr(x):
    t = _type(x)
    if t == 1:
        return _concat(_concat("'", x), "'")
    if t == 2 or t == 5:
        n = len(x)
        s = "["
        if t == 5:
            s = "("
        i = 0
        while i < n:
            if i > 0:
                s = _concat(s, ", ")
            s = _concat(s, _repr(_lget(x, i)))
            i = i + 1
        if t == 5:
            if n == 1:
                s = _concat(s, ",")
            return _concat(s, ")")
        return _concat(s, "]")
    if t == 9:
        n = len(x)
        if n == 0:
            return "set()"
        s = "{"
        i = 0
        while i < n:
            if i > 0:
                s = _concat(s, ", ")
            s = _concat(s, _repr(_lget(x, i)))
            i = i + 1
        return _concat(s, "}")
    if t == 8:
        return "<function>"
    if t == 3:
        keys = _dkeys(x)
        vals = _dvals(x)
        n = len(keys)
        s = "{"
        i = 0
        while i < n:
            if i > 0:
                s = _concat(s, ", ")
            s = _concat(s, _concat(_repr(_lget(keys, i)), _concat(": ", _repr(_lget(vals, i)))))
            i = i + 1
        return _concat(s, "}")
    return _str(x)


def _is_space(c):
    return c == 32 or c == 9 or c == 10 or c == 13


def _int(x, base=10):
    t = _type(x)
    if t == 0:
        return x
    if t == 7:
        return _bval(x)
    if t == 4:
        return _f2i(x)
    if t != 1:
        _error("int() needs a number or a text")
    n = len(x)
    i = 0
    while i < n and _is_space(_sget(x, i)):
        i = i + 1
    neg = 0
    if i < n and (_sget(x, i) == 45 or _sget(x, i) == 43):
        if _sget(x, i) == 45:
            neg = 1
        i = i + 1
    if base == 16 and i + 1 < n and _sget(x, i) == 48 and (_sget(x, i + 1) == 120 or _sget(x, i + 1) == 88):
        i = i + 2
    v = 0
    seen = 0
    while i < n:
        c = _sget(x, i)
        d = -1
        if c >= 48 and c <= 57:
            d = c - 48
        elif c >= 97 and c <= 102:
            d = c - 87
        elif c >= 65 and c <= 70:
            d = c - 55
        if d < 0 or d >= base:
            break
        v = v * base + d
        seen = 1
        i = i + 1
    while i < n and _is_space(_sget(x, i)):
        i = i + 1
    if seen == 0 or i < n:
        _raise("ValueError", "invalid literal for int() with base " + _int_str(base) + ": " + _repr(x))
    if neg == 1:
        v = 0 - v
    return v


def _float(x):
    t = _type(x)
    if t == 4:
        return x
    if t == 0:
        return _i2f(x)
    if t == 7:
        return _i2f(_bval(x))
    if t != 1:
        _error("float() needs a number or a text")
    n = len(x)
    i = 0
    while i < n and _is_space(_sget(x, i)):
        i = i + 1
    neg = 0
    if i < n and (_sget(x, i) == 45 or _sget(x, i) == 43):
        if _sget(x, i) == 45:
            neg = 1
        i = i + 1
    v = 0.0
    seen = 0
    while i < n and _sget(x, i) >= 48 and _sget(x, i) <= 57:
        v = _fadd(_fmul(v, 10.0), _i2f(_sget(x, i) - 48))
        seen = 1
        i = i + 1
    if i < n and _sget(x, i) == 46:
        i = i + 1
        scale = 0.1
        while i < n and _sget(x, i) >= 48 and _sget(x, i) <= 57:
            v = _fadd(v, _fmul(scale, _i2f(_sget(x, i) - 48)))
            scale = _fdiv(scale, 10.0)
            seen = 1
            i = i + 1
    while i < n and _is_space(_sget(x, i)):
        i = i + 1
    if seen == 0 or i < n:
        _raise("ValueError", "could not convert string to float: " + _repr(x))
    if neg == 1:
        v = _fsub(0.0, v)
    return v


def _bool(x):
    if x:
        return True
    return False


def _chr(n):
    r = _str_new(1)
    _sset(r, 0, n)
    return r


def _ord(s):
    if _type(s) != 1 or len(s) != 1:
        _error("ord() needs a text of one letter")
    return _sget(s, 0)


def _pad(s, width, fill, left):
    while len(s) < width:
        if left:
            s = _concat(s, fill)
        else:
            s = _concat(fill, s)
    return s


def _hex(n):
    if n == 0:
        return "0"
    neg = ""
    if n < 0:
        neg = "-"
        n = 0 - n
    s = ""
    while n > 0:
        d = n % 16
        if d < 10:
            s = _concat(_chr(48 + d), s)
        else:
            s = _concat(_chr(87 + d), s)
        n = n // 16
    return _concat(neg, s)


def _fixed(f, places):
    f = _tofloat(f)
    sign = ""
    if _flt(f, 0.0):
        sign = "-"
        f = _fsub(0.0, f)
    scale = 1
    k = 0
    while k < places:
        scale = scale * 10
        k = k + 1
    whole = _f2i(f)
    frac = _f2i(_fadd(_fmul(_fsub(f, _i2f(whole)), _i2f(scale)), 0.5))
    if frac >= scale:
        whole = whole + 1
        frac = frac - scale
    s = _concat(sign, _int_str(whole))
    if places > 0:
        s = _concat(_concat(s, "."), _pad(_int_str(frac), places, "0", False))
    return s


def _fmt(v, spec):
    # what stands after the ':' in an f-string:  [fill][< > ^][0][width][.places][d f x s]
    if spec is None or len(spec) == 0:
        return _str(v)
    n = len(spec)
    i = 0
    fill = " "
    align = 0
    if n >= 2 and (_sget(spec, 1) == 60 or _sget(spec, 1) == 62 or _sget(spec, 1) == 94):
        fill = _chr(_sget(spec, 0))
        align = _sget(spec, 1)
        i = 2
    elif _sget(spec, 0) == 60 or _sget(spec, 0) == 62 or _sget(spec, 0) == 94:
        align = _sget(spec, 0)
        i = 1
    if i < n and _sget(spec, i) == 48:
        fill = "0"
        if align == 0:
            align = 62
        i = i + 1
    width = 0
    while i < n and _sget(spec, i) >= 48 and _sget(spec, i) <= 57:
        width = width * 10 + _sget(spec, i) - 48
        i = i + 1
    places = -1
    if i < n and _sget(spec, i) == 46:
        i = i + 1
        places = 0
        while i < n and _sget(spec, i) >= 48 and _sget(spec, i) <= 57:
            places = places * 10 + _sget(spec, i) - 48
            i = i + 1
    kind = 0
    if i < n:
        kind = _sget(spec, i)
    t = _type(v)
    if kind == 102:
        if places < 0:
            places = 6
        s = _fixed(v, places)
    elif kind == 120:
        s = _hex(_int(v))
    elif kind == 88:
        s = _m_upper(_hex(_int(v)))
    elif places >= 0 and t == 4:
        s = _fixed(v, places)
    else:
        s = _str(v)
    if align == 0:
        if t == 1:
            align = 60
        else:
            align = 62
    if align == 94:
        total = width - len(s)
        if total > 0:
            s = _pad(s, len(s) + total // 2, fill, False)
        return _pad(s, width, fill, True)
    return _pad(s, width, fill, align == 60)


def _print(items, sep, end):
    n = len(items)
    s = ""
    i = 0
    while i < n:
        if i > 0:
            s = _concat(s, sep)
        s = _concat(s, _str(_lget(items, i)))
        i = i + 1
    _write(_concat(s, end))
    return None


def _input(prompt=""):
    _write(_str(prompt))
    return _readline()


# ---------------------------------------------------------------- the built-in functions

def _iter(x):
    # what a for loop walks over
    t = _type(x)
    if t == 3:
        return _copy_items(_dkeys(x))
    if t == 9:
        return _copy_items(x)
    if t == 1 or t == 2 or t == 5:
        return x
    _raise("TypeError", "for ... in needs a text, a list, a tuple, a set, a dict or range()")


def _copy_items(x):
    n = len(x)
    r = _list_new(n)
    i = 0
    while i < n:
        _push(r, _lget(x, i))
        i = i + 1
    return r


def _len(x):
    return len(x)


def _map(f, seq):
    s = _iter(seq)
    n = len(s)
    r = _list_new(n)
    i = 0
    while i < n:
        _push(r, f(s[i]))
        i = i + 1
    return r


def _filter(f, seq):
    s = _iter(seq)
    n = len(s)
    r = _list_new(n)
    i = 0
    while i < n:
        if f is None:
            if s[i]:
                _push(r, s[i])
        elif f(s[i]):
            _push(r, s[i])
        i = i + 1
    return r


def _range_list(start, stop, step):
    if step == 0:
        _error("range(): the step cannot be 0")
    r = _list_new(8)
    i = start
    if step > 0:
        while i < stop:
            _push(r, i)
            i = i + step
    else:
        while i > stop:
            _push(r, i)
            i = i + step
    return r


def _list(x=None):
    r = _list_new(8)
    if x is None:
        return r
    s = _iter(x)
    n = len(s)
    i = 0
    while i < n:
        _push(r, s[i])
        i = i + 1
    return r


def _tuple(x=None):
    return _settype(_list(x), 5)


def _dict(x=None):
    d = {}
    if x is None:
        return d
    if _type(x) == 3:
        _m_update(d, x)
        return d
    n = len(x)
    i = 0
    while i < n:
        pair = x[i]
        _dict_set(d, pair[0], pair[1])
        i = i + 1
    return d


def _abs(x):
    if x < 0:
        return 0 - x
    return x


def _best(seq, key, biggest):
    s = _iter(seq)
    n = len(s)
    if n == 0:
        _raise("ValueError", "min() or max() of nothing")
    m = s[0]
    km = m
    if key is not None:
        km = key(m)
    i = 1
    while i < n:
        k = s[i]
        if key is not None:
            k = key(k)
        if (biggest and k > km) or (not biggest and k < km):
            m = s[i]
            km = k
        i = i + 1
    return m


def _min(seq, key=None):
    return _best(seq, key, False)


def _max(seq, key=None):
    return _best(seq, key, True)


def _sum(seq, start=0):
    s = _iter(seq)
    n = len(s)
    i = 0
    while i < n:
        start = start + s[i]
        i = i + 1
    return start


def _any(seq):
    s = _iter(seq)
    n = len(s)
    i = 0
    while i < n:
        if s[i]:
            return True
        i = i + 1
    return False


def _all(seq):
    s = _iter(seq)
    n = len(s)
    i = 0
    while i < n:
        if not s[i]:
            return False
        i = i + 1
    return True


def _sorted(seq, key=None, reverse=False):
    r = _list(seq)
    _m_sort(r, key, reverse)
    return r


def _reversed(seq):
    r = _list(seq)
    _m_reverse(r)
    return r


def _enumerate(seq, start=0):
    s = _iter(seq)
    n = len(s)
    r = _list_new(n)
    i = 0
    while i < n:
        _push(r, (start + i, s[i]))
        i = i + 1
    return r


def _zip(a, b):
    sa = _iter(a)
    sb = _iter(b)
    n = len(sa)
    if len(sb) < n:
        n = len(sb)
    r = _list_new(n)
    i = 0
    while i < n:
        _push(r, (sa[i], sb[i]))
        i = i + 1
    return r


def _divmod(a, b):
    return (a // b, a % b)


def _round(x, places=0):
    if _type(x) != 4:
        return x
    if places == 0:
        if _flt(x, 0.0):
            return 0 - _f2i(_fadd(_fsub(0.0, x), 0.5))
        return _f2i(_fadd(x, 0.5))
    return _float(_fixed(x, places))


def _assert_fail(msg):
    _error(_concat("assert: ", _str(msg)))


# ---------------------------------------------------------------- methods of lists

def _need(o, kind, what):
    if _type(o) != kind:
        _error(what)
    return None


def _m_append(l, v):
    _need(l, 2, ".append() is for a list")
    _push(l, v)
    return None


def _m_extend(l, other):
    _need(l, 2, ".extend() is for a list")
    s = _iter(other)
    n = len(s)
    i = 0
    while i < n:
        _push(l, s[i])
        i = i + 1
    return None


def _m_insert(l, i, v):
    _need(l, 2, ".insert() is for a list")
    n = len(l)
    if i < 0:
        i = i + n
    if i < 0:
        i = 0
    if i > n:
        i = n
    _push(l, v)
    k = n
    while k > i:
        _lset(l, k, _lget(l, k - 1))
        k = k - 1
    _lset(l, i, v)
    return None


def _m_pop(o, i=None):
    t = _type(o)
    if t == 3:
        k = _dict_find(o, i)
        if k < 0:
            _raise("KeyError", _repr(i))
        v = _lget(_dvals(o), k)
        _remove_at(_dkeys(o), k)
        _remove_at(_dvals(o), k)
        return v
    if t != 9:
        _need(o, 2, ".pop() is for a list, a set or a dict")
    n = len(o)
    if n == 0:
        _raise("IndexError", ".pop() from an empty list")
    if i is None:
        i = n - 1
    if i < 0:
        i = i + n
    if i < 0 or i >= n:
        _raise("IndexError", ".pop(): the index is outside the list")
    v = _lget(o, i)
    _remove_at(o, i)
    return v


def _m_remove(l, v):
    if _type(l) != 9:
        _need(l, 2, ".remove() is for a list or a set")
    n = len(l)
    i = 0
    while i < n:
        if _lget(l, i) == v:
            _remove_at(l, i)
            return None
        i = i + 1
    _raise("ValueError", ".remove(): the value is not there")


def _m_index(o, v):
    t = _type(o)
    if t == 1:
        i = _find_text(o, v, 0)
        if i < 0:
            _raise("ValueError", ".index(): the text is not there")
        return i
    n = len(o)
    i = 0
    while i < n:
        if _lget(o, i) == v:
            return i
        i = i + 1
    _raise("ValueError", ".index(): the value is not in the list")


def _m_count(o, v):
    t = _type(o)
    c = 0
    if t == 1:
        i = _find_text(o, v, 0)
        step = len(v)
        if step == 0:
            return len(o) + 1
        while i >= 0:
            c = c + 1
            i = _find_text(o, v, i + step)
        return c
    n = len(o)
    i = 0
    while i < n:
        if _lget(o, i) == v:
            c = c + 1
        i = i + 1
    return c


def _m_reverse(l):
    _need(l, 2, ".reverse() is for a list")
    i = 0
    j = len(l) - 1
    while i < j:
        v = _lget(l, i)
        _lset(l, i, _lget(l, j))
        _lset(l, j, v)
        i = i + 1
        j = j - 1
    return None


def _m_sort(l, key=None, reverse=False):
    # a merge of sorted halves would be faster; this keeps equal values in their order
    _need(l, 2, ".sort() is for a list")
    n = len(l)
    keys = l
    if key is not None:
        keys = _list_new(n)
        i = 0
        while i < n:
            _push(keys, key(_lget(l, i)))
            i = i + 1
    i = 1
    while i < n:
        v = _lget(l, i)
        kv = _lget(keys, i)
        j = i - 1
        while j >= 0 and ((not reverse and _lget(keys, j) > kv) or (reverse and _lget(keys, j) < kv)):
            _lset(l, j + 1, _lget(l, j))
            if key is not None:
                _lset(keys, j + 1, _lget(keys, j))
            j = j - 1
        _lset(l, j + 1, v)
        if key is not None:
            _lset(keys, j + 1, kv)
        i = i + 1
    return None


def _m_clear(o):
    t = _type(o)
    if t == 3:
        _lsetlen(_dkeys(o), 0)
        _lsetlen(_dvals(o), 0)
        return None
    if t != 9:
        _need(o, 2, ".clear() is for a list, a set or a dict")
    _lsetlen(o, 0)
    return None


def _m_copy(o):
    t = _type(o)
    if t == 3:
        d = {}
        _m_update(d, o)
        return d
    if t == 9:
        return _settype(_copy_items(o), 9)
    return _slice(o, None, None, None)


# ---------------------------------------------------------------- methods of texts

def _m_upper(s):
    n = len(s)
    r = _str_new(n)
    i = 0
    while i < n:
        c = _sget(s, i)
        if c >= 97 and c <= 122:
            c = c - 32
        _sset(r, i, c)
        i = i + 1
    return r


def _m_lower(s):
    n = len(s)
    r = _str_new(n)
    i = 0
    while i < n:
        c = _sget(s, i)
        if c >= 65 and c <= 90:
            c = c + 32
        _sset(r, i, c)
        i = i + 1
    return r


def _strip_set(c, chars):
    if chars is None:
        return _is_space(c)
    return _find_text(chars, _chr(c), 0) >= 0


def _m_strip(s, chars=None):
    return _m_lstrip(_m_rstrip(s, chars), chars)


def _m_lstrip(s, chars=None):
    n = len(s)
    i = 0
    while i < n and _strip_set(_sget(s, i), chars):
        i = i + 1
    return _slice(s, i, n, 1)


def _m_rstrip(s, chars=None):
    n = len(s)
    while n > 0 and _strip_set(_sget(s, n - 1), chars):
        n = n - 1
    return _slice(s, 0, n, 1)


def _m_find(s, sub, start=0):
    return _find_text(s, sub, start)


def _m_startswith(s, prefix):
    if len(prefix) > len(s):
        return False
    return _slice(s, 0, len(prefix), 1) == prefix


def _m_endswith(s, suffix):
    n = len(s)
    m = len(suffix)
    if m > n:
        return False
    return _slice(s, n - m, n, 1) == suffix


def _m_replace(s, old, new):
    m = len(old)
    if m == 0:
        return s
    r = ""
    start = 0
    i = _find_text(s, old, 0)
    while i >= 0:
        r = _concat(_concat(r, _slice(s, start, i, 1)), new)
        start = i + m
        i = _find_text(s, old, start)
    return _concat(r, _slice(s, start, len(s), 1))


def _m_split(s, sep=None):
    r = _list_new(8)
    n = len(s)
    if sep is None:
        i = 0
        while i < n:
            while i < n and _is_space(_sget(s, i)):
                i = i + 1
            if i >= n:
                break
            j = i
            while j < n and not _is_space(_sget(s, j)):
                j = j + 1
            _push(r, _slice(s, i, j, 1))
            i = j
        return r
    m = len(sep)
    if m == 0:
        _error(".split(): the separator is empty")
    start = 0
    i = _find_text(s, sep, 0)
    while i >= 0:
        _push(r, _slice(s, start, i, 1))
        start = i + m
        i = _find_text(s, sep, start)
    _push(r, _slice(s, start, n, 1))
    return r


def _m_join(sep, seq):
    s = _iter(seq)
    n = len(s)
    r = ""
    i = 0
    while i < n:
        if _type(s[i]) != 1:
            _error(".join() needs texts - use str()")
        if i > 0:
            r = _concat(r, sep)
        r = _concat(r, s[i])
        i = i + 1
    return r


def _all_chars(s, lo1, hi1, lo2, hi2):
    n = len(s)
    if n == 0:
        return False
    i = 0
    while i < n:
        c = _sget(s, i)
        if not ((c >= lo1 and c <= hi1) or (c >= lo2 and c <= hi2)):
            return False
        i = i + 1
    return True


def _m_isdigit(s):
    return _all_chars(s, 48, 57, 48, 57)


def _m_isalpha(s):
    return _all_chars(s, 65, 90, 97, 122)


def _m_isspace(s):
    return _all_chars(s, 9, 13, 32, 32)


# ---------------------------------------------------------------- methods of dicts

def _m_get(d, k, default=None):
    i = _dict_find(d, k)
    if i < 0:
        return default
    return _lget(_dvals(d), i)


def _m_keys(d):
    return _m_copy(_dkeys(d))


def _m_values(d):
    return _m_copy(_dvals(d))


def _m_items(d):
    keys = _dkeys(d)
    vals = _dvals(d)
    n = len(keys)
    r = _list_new(n)
    i = 0
    while i < n:
        _push(r, (_lget(keys, i), _lget(vals, i)))
        i = i + 1
    return r


def _m_update(d, other):
    if _type(d) == 9:
        s = _iter(other)
        n = len(s)
        i = 0
        while i < n:
            _m_add(d, s[i])
            i = i + 1
        return None
    keys = _dkeys(other)
    vals = _dvals(other)
    n = len(keys)
    i = 0
    while i < n:
        _dict_set(d, _lget(keys, i), _lget(vals, i))
        i = i + 1
    return None


def _m_setdefault(d, k, v=None):
    i = _dict_find(d, k)
    if i < 0:
        _dict_set(d, k, v)
        return v
    return _lget(_dvals(d), i)


# ---------------------------------------------------------------- sets: a list where every value is once

def _set(x=None):
    r = _settype(_list_new(8), 9)
    if x is not None:
        _m_update(r, x)
    return r


def _m_add(s, v):
    _need(s, 9, ".add() is for a set")
    if not _contains(s, v):
        _push(s, v)
    return None


def _m_discard(s, v):
    _need(s, 9, ".discard() is for a set")
    n = len(s)
    i = 0
    while i < n:
        if _lget(s, i) == v:
            _remove_at(s, i)
            return None
        i = i + 1
    return None


def _m_union(a, b):
    r = _set(a)
    _m_update(r, b)
    return r


def _m_intersection(a, b):
    r = _set()
    s = _iter(a)
    n = len(s)
    i = 0
    while i < n:
        if _contains(b, s[i]):
            _push(r, s[i])
        i = i + 1
    return r


def _m_difference(a, b):
    r = _set()
    s = _iter(a)
    n = len(s)
    i = 0
    while i < n:
        if not _contains(b, s[i]):
            _push(r, s[i])
        i = i + 1
    return r


def _m_issubset(a, b):
    return len(_m_difference(a, b)) == 0


def _m_issuperset(a, b):
    return len(_m_difference(b, a)) == 0


def _bitop(a, b, op):
    # & | ^ on what is not two whole numbers.  op: 0 &   1 |   2 ^
    ta = _type(a)
    tb = _type(b)
    if ta == 9 and tb == 9:
        if op == 0:
            return _m_intersection(a, b)
        if op == 1:
            return _m_union(a, b)
        return _m_union(_m_difference(a, b), _m_difference(b, a))
    if (ta == 7 or ta == 0) and (tb == 7 or tb == 0):
        x = a
        y = b
        if ta == 7:
            x = _bval(a)
        if tb == 7:
            y = _bval(b)
        if op == 0:
            r = x & y
        elif op == 1:
            r = x | y
        else:
            r = x ^ y
        if ta == 7 and tb == 7:
            return r == 1
        return r
    _raise("TypeError", "& | ^ need whole numbers or sets")

# ---------------------------------------------------------------- from the PyTon of v2.9
# (the programs of apps/ use these; in new programs chr(), ord() and .split() do the same)

def char(n):
    return _chr(n)


def code(s, i=0):
    if _type(s) != 1 or i < 0 or i >= len(s):
        return 0
    return _sget(s, i)


def field(s, sep, index):
    # the part number index of s, cut at the letter with the code sep
    n = len(s)
    start = 0
    k = 0
    i = 0
    while i < n:
        if _sget(s, i) == sep:
            if k == index:
                return _slice(s, start, i, 1)
            k = k + 1
            start = i + 1
        i = i + 1
    if k == index:
        return _slice(s, start, n, 1)
    return ""


def textof(codes):
    # a list of letter codes -> a text (the programs of v2.9 keep typed text as such a list)
    n = len(codes)
    r = _str_new(n)
    i = 0
    while i < n:
        _sset(r, i, _lget(codes, i))
        i = i + 1
    return r


def textl(x, y, codes, start, count, colour):
    # draw count letters of a list of letter codes, from number start (as the PyTon of v2.9 did)
    n = len(codes)
    if start < 0:
        start = 0
    if count > n - start:
        count = n - start
    if count > 255:
        count = 255
    if count < 0:
        count = 0
    r = _str_new(count)
    i = 0
    while i < count:
        c = _lget(codes, start + i)
        if c < 32:
            c = 32
        _sset(r, i, c)
        i = i + 1
    text(x, y, r, colour)
    return None
