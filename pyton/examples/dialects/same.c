/* same.c - written as C */
#include <stdio.h>

int total = 0;

int fib(int n) {
    if (n < 2) return n;
    return fib(n - 1) + fib(n - 2);
}

int add(int k) {
    total += k;
    return total;
}

int main(void) {
    printf("%d\n", 2 + 2);
    for (int i = 0; i < 10; i++) {
        if (i == 3) continue;
        if (i > 7) break;
        add(i * i);
    }
    printf("total %d\n", total);
    int a[] = {5, 3, 9, 1};
    int best = a[0];
    for (int k = 1; k < 4; k++) {
        if (a[k] > best) best = a[k];
    }
    printf("biggest %d of %d\n", best, 4);
    printf("%d %s %d\n", 7 / 2, "3.5", 7 % 3);
    printf("fib(15) = %d, %s\n", fib(15), "NinuxOS");
    int x = 10;
    do { x -= 3; } while (x > 0);
    printf("%d %d\n", x, x < 0 ? 1 : 0);
    return 0;
}
