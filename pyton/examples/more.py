# more.py - try / except, lambda, def inside def, *args, sets, functions as values.
# Runs the same under real Python (see pyton/test.py).

def total(*numbers):
    s = 0
    for n in numbers:
        s += n
    return s


def join_all(sep, *parts):
    return sep.join([str(p) for p in parts])


def make_adder(k):
    def add(x):
        return x + k
    return add


def make_counter():
    state = [0]

    def step(by=1):
        state[0] += by
        return state[0]
    return step


def fib(n):
    def go(a, b, left):
        if left == 0:
            return a
        return go(b, a + b, left - 1)
    return go(0, 1, n)


def safe_div(a, b):
    try:
        return a / b
    except ZeroDivisionError:
        return None
    finally:
        print("  safe_div", a, b)


def parse(texts):
    good = []
    bad = 0
    for t in texts:
        try:
            good.append(int(t))
        except ValueError as e:
            bad += 1
            print("  not a number:", e)
    return good, bad


def check(age):
    if age < 0:
        raise ValueError("age below zero")
    return age


def apply(f, values):
    return [f(v) for v in values]


# *args
print(total(), total(1), total(1, 2, 3), join_all("-", 1, "two", 3.5), total(*[4, 5, 6]))

# functions as values, lambda, def inside def
add5 = make_adder(5)
double = lambda x: x * 2
print(add5(1), make_adder(100)(1), double(21), apply(double, [1, 2, 3]), apply(add5, (10, 20)))
counter = make_counter()
print(counter(), counter(), counter(10), fib(10), fib(30))
ops = {"+": lambda a, b: a + b, "*": lambda a, b: a * b}
print(ops["+"](2, 3), ops["*"](2, 3), list(map(str, [1, 2])), list(filter(lambda n: n % 2, range(7))))
words = ["pear", "fig", "banana", "kiwi"]
print(sorted(words), sorted(words, key=len), sorted(words, key=len, reverse=True), max(words, key=len))
words.sort(key=lambda w: w[-1])
print(words, min(3, 1, 2), max([4, 9, 2]), sum(n * n for n in range(4)))

# try / except
print(safe_div(1, 2), safe_div(1, 0))
print(parse(["1", "x", "30", "4.5", " 7 "]))
try:
    check(5)
    check(-1)
    print("not reached")
except ValueError as e:
    print("caught:", e)
else:
    print("no error")
try:
    [1, 2, 3][10]
except IndexError:
    print("index")
try:
    {"a": 1}["b"]
except (KeyError, IndexError) as e:
    print("key", e)
try:
    try:
        raise RuntimeError("inner")
    finally:
        print("cleanup")
except Exception as e:
    print("outer got:", e)
for attempt in range(4):
    try:
        if attempt == 1:
            continue
        if attempt == 3:
            break
        print("attempt", attempt)
    finally:
        print("  after", attempt)
try:
    assert 1 + 1 == 3, "arithmetic is broken"
except AssertionError as e:
    print("assert:", e)

# sets and the other comprehensions
a = {1, 2, 3, 2, 1}
b = set([3, 4])
a.add(10)
a.discard(2)
print(sorted(a), len(a), 3 in a, 2 in a, sorted(a | b), sorted(a & b), sorted(a - b), sorted(a ^ b))
print(sorted({w[0] for w in words}), {w: len(w) for w in sorted(words)}, len(set("mississippi")))
print(set() == set(), {1, 2} == {2, 1}, a.issubset({1, 3, 10, 99}), True & False, True | False)
