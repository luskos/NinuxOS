// same.cpp - written as C++
#include <iostream>
using namespace std;

int total = 0;

int fib(int n) {
    if (n < 2) return n;
    return fib(n - 1) + fib(n - 2);
}

int add(int k) {
    total += k;
    return total;
}

int main() {
    cout << 2 + 2 << endl;
    for (int i = 0; i < 10; i++) {
        if (i == 3) continue;
        if (i > 7) break;
        add(i * i);
    }
    cout << "total " << total << endl;
    int a[] = {5, 3, 9, 1};
    int best = a[0];
    for (int k = 1; k < 4; k++) {
        if (a[k] > best) best = a[k];
    }
    cout << "biggest " << best << " of " << 4 << endl;
    double seven = 7.0;
    cout << 7 / 2 << " " << seven / 2 << " " << 7 % 3 << endl;
    string name = "Ninux";
    name += "OS";
    cout << "fib(15) = " << fib(15) << ", " << name << endl;
    int x = 10;
    do { x -= 3; } while (x > 0);
    cout << x << " " << (x < 0 ? 1 : 0) << endl;
    return 0;
}
