# garbage.py - memory that is no longer used must come back (v3.0.20).
# About 400 MB are made and dropped while a few things are kept; the program must end with what
# it kept intact, and must not have asked the system for more than a little.
keep = []
total = 0
for i in range(40000):
    line = [i, str(i), "x" * (i % 50), {"n": i, "half": i / 2}, (i, i + 1)]
    words = ("word" + str(i) + " ") * 20
    parts = words.split()
    total = total + len(parts) + len(line) + len(sorted(parts))
    if i % 4000 == 0:
        keep.append(line)
        keep.append(parts[:3])
print(total, len(keep))
for k in keep[:6]:
    print(k)
print(keep[-2][1], keep[-2][3]["half"], keep[-1])
big = [n * n for n in range(200000)]
big = [n for n in big if n % 3 == 0]
print(len(big), big[-1], sum(big) % 1000003)
texts = {}
for i in range(20000):
    texts[i % 100] = "value " + str(i) + " " + str(i * 7)
print(len(texts), texts[0], texts[99])
try:
    used = memory()
except NameError:                       # Python itself: no such function
    used = 0
if used < 48 * 1024 * 1024:
    print("memory: little was asked from the system")
else:
    print("memory: too much asked from the system:", used)
