// same.cs - written as C#
using System;

class Program {
    static int total = 0;

    static int Fib(int n) {
        if (n < 2) return n;
        return Fib(n - 1) + Fib(n - 2);
    }

    static int Add(int k) {
        total += k;
        return total;
    }

    static void Main() {
        Console.WriteLine(2 + 2);
        for (int i = 0; i < 10; i++) {
            if (i == 3) continue;
            if (i > 7) break;
            Add(i * i);
        }
        Console.WriteLine("total " + total);
        int[] a = {5, 3, 9, 1};
        int best = a[0];
        for (int k = 1; k < a.Length; k++) {
            if (a[k] > best) best = a[k];
        }
        Console.WriteLine("biggest " + best + " of " + a.Length);
        double seven = 7.0;
        Console.WriteLine($"{7 / 2} {seven / 2} {7 % 3}");
        string name = "Ninux";
        name += "OS";
        Console.WriteLine("fib(15) = " + Fib(15) + ", " + name);
        int x = 10;
        do { x -= 3; } while (x > 0);
        Console.WriteLine(x + " " + (x < 0 ? 1 : 0));
    }
}
