# basics.py - one of everything the new py2asm compiles. The same file runs under real Python:
# the two outputs should be the same (fractions: PyTon shows up to 6 digits after the point).
#
#   python pyton/examples/basics.py > python.txt
#   python pyton/py2asm.py pyton/examples/basics.py
#   nasm -f win64 -I pyton/ pyton/examples/basics.asm -o basics.obj
#   gcc basics.obj -o basics.exe
#   basics.exe > pyton.txt

total = 0


def add(a, b=10):
    return a + b


def count_up(n):
    global total
    for i in range(n):
        total += i
    return total


def fact(n):
    if n <= 1:
        return 1
    return n * fact(n - 1)


def describe(name, age=0, city="Sofia"):
    return f"{name} is {age} and lives in {city}"


# numbers
x = 7
y = 2
print("numbers:", x + y, x - y, x * y, x // y, x % y, x ** y, -x // y, -x % y)
print("fractions:", x / y, 0.5 + 0.25, 10 / 4, 2 ** 0.5 > 1.4)
print("bits:", x & 3, x | 8, x ^ 1, x << 2, x >> 1, ~x)
print("compare:", 1 < 2 < 3, 1 < 2 > 5, x == 7, x != 7, not x, x and y, 0 or "empty")

# texts
s = "Hello, NinuxOS"
print(s, len(s), s[0], s[-1], s[7:], s[:5], s[::-1])
print(s.upper(), s.lower(), s.replace("Hello", "Bye"), s.find("Ninux"), "Ninux" in s)
print("a,b,c".split(","), " ".join(["x", "y", "z"]), "  trim  ".strip() + "|", "ab" * 3)
print(s.startswith("Hello"), s.endswith("OS"), "123".isdigit(), int("42") + 1, str(42) + "!")

# lists
nums = [5, 3, 8, 1]
nums.append(9)
nums.insert(0, 7)
print(nums, len(nums), nums[1:3], sum(nums), min(nums), max(nums), sorted(nums))
nums.sort()
last = nums.pop()
nums.remove(3)
print(nums, last, nums.index(8), 8 in nums, [n * n for n in nums if n % 2 == 1])
nums[0] = 100
nums[1] += 1
print(nums, nums + [1, 2], list(range(3)), list(range(10, 0, -3)))

# tuples and dicts
point = (3, 4)
px, py = point
px, py = py, px
print(point, px, py)
ages = {"Ana": 31, "Boris": 25}
ages["Vera"] = 40
ages["Ana"] += 1
print(ages, len(ages), ages["Ana"], ages.get("Nobody", -1), "Boris" in ages)
for name in ages:
    print(" ", name, ages[name])
for name, age in ages.items():
    if age > 30:
        print("  over 30:", name)
del ages["Boris"]
print(list(ages.keys()), list(ages.values()))

# loops
i = 0
while True:
    i += 1
    if i == 3:
        continue
    if i > 5:
        break
    print("i =", i)
for n, letter in enumerate("abc"):
    print(n, letter, end="; ")
print()
for a, b in zip([1, 2, 3], ["one", "two", "three"]):
    print(a, b)
for n in range(2, 10):
    if n % 7 == 0:
        print("found", n)
        break
else:
    print("no multiple of 7")

# functions
print(add(1), add(1, 2), add(b=5, a=1), count_up(5), total, fact(10))
print(describe("Ana"), "/", describe("Boris", city="Varna", age=25))
print(f"{3.14159:.2f} {42:>6} {'left':<8}| {255:x} {7:03d}")
print("big" if x > 5 else "small", abs(-3), round(2.6), divmod(17, 5), bool(""), None)
