# pyhello.py - the first program compiled by the new py2asm for NinuxOS itself.
# In the shell:  run pyhello          run pyhello numbers
META = {"type": "demo", "label": "PyHello", "sockets": "run,numbers"}

visits = 0


def run():
    global visits
    visits += 1
    print("Hello from the new py2asm! I was run", visits, "time(s).")
    print("My type is", meta("type") + ", my name is", meta("name"))
    log("pyhello: run " + str(visits))
    return visits


def numbers():
    squares = [n * n for n in range(1, 8)]
    words = {"one": 1, "two": 2}
    try:
        words["three"]
    except KeyError as e:
        print("no key", e)
    print(squares, sum(squares), sorted(words, key=len), 7 / 2, f"{255:x}")
    return len(squares)
