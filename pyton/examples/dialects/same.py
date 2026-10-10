# same.py - the program the five dialects below also are; all six must print the same.
def fib(n):
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)

total = 0

def add(k):
    global total
    total += k
    return total

def main():
    print(2 + 2)
    i = 0
    while i < 10:
        if i == 3:
            i += 1
            continue
        if i > 7:
            break
        add(i * i)
        i += 1
    print("total", total)
    a = [5, 3, 9, 1]
    best = a[0]
    k = 1
    while k < 4:
        if a[k] > best:
            best = a[k]
        k += 1
    print("biggest " + str(best) + " of " + str(len(a)))
    print(7 // 2, 7.0 / 2, 7 % 3)
    name = "Ninux"
    name += "OS"
    print("fib(15) = " + str(fib(15)) + ", " + name)
    x = 10
    while True:
        x -= 3
        if not (x > 0):
            break
    print(x, (1 if x < 0 else 0))

main()
