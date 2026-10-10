// Same.java - written as Java
public class Same {
    static int total = 0;

    static int fib(int n) {
        if (n < 2) return n;
        return fib(n - 1) + fib(n - 2);
    }

    static int add(int k) {
        total += k;
        return total;
    }

    public static void main(String[] args) {
        System.out.println(2 + 2);
        for (int i = 0; i < 10; i++) {
            if (i == 3) continue;
            if (i > 7) break;
            add(i * i);
        }
        System.out.println("total " + total);
        int[] a = {5, 3, 9, 1};
        int best = a[0];
        for (int k = 1; k < a.length; k++) {
            if (a[k] > best) best = a[k];
        }
        System.out.println("biggest " + best + " of " + a.length);
        double seven = 7.0;
        System.out.println(7 / 2 + " " + seven / 2 + " " + 7 % 3);
        String name = "Ninux";
        name += "OS";
        System.out.println("fib(15) = " + fib(15) + ", " + name);
        int x = 10;
        do { x -= 3; } while (x > 0);
        System.out.println(x + " " + (x < 0 ? 1 : 0));
    }
}
