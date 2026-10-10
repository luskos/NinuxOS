// same.js - written as JavaScript
let total = 0;

function fib(n) {
    if (n < 2) return n;
    return fib(n - 1) + fib(n - 2);
}

function add(k) {
    total += k;
    return total;
}

function main() {
    console.log(2 + 2);
    for (let i = 0; i < 10; i++) {
        if (i === 3) continue;
        if (i > 7) break;
        add(i * i);
    }
    console.log("total", total);
    const a = [5, 3, 9, 1];
    let best = a[0];
    for (let k = 1; k < a.length; k++) {
        if (a[k] > best) best = a[k];
    }
    console.log("biggest " + best + " of " + a.length);
    console.log(Math.floor(7 / 2), 7 / 2, 7 % 3);
    let name = "Ninux";
    name += "OS";
    console.log(`fib(15) = ${fib(15)}, ${name}`);
    let x = 10;
    do { x -= 3; } while (x > 0);
    console.log(x, x < 0 ? 1 : 0);
}

main();
