I'm currently reading the awesome book ["Crafting Interpreters"](https://craftinginterpreters.com/) by Rober Nystrom, in which he describes how to write an interpreter for Lox as an example language.

This is pretty much the implementation he describes written in Python.
I also implemented some of the challenges (like ternery expressions, nameless functions, ...).

Still work in progess...

Additional features:
- ternery operator:
  `condition ? then_expr : else_expr`
- nameless functions:
  `fun (arg) { do_something; }`
- 'static' methods, callable on a class not an instance
- implicit conversion to str if numbers and strings are added
  `4+'foo' == '4foo'`
- `break` statement to break out of loops
- multi inheritance:
  ```
  class SuperA {
    foo(bar) {
      print "SuperA: " + bar;
    }
  }
  class SuperB {
    foo() {
      print "SuperB";
    }
  }
  class C < SuperA, SuperB {
    foo(bar) {
      super(SuperA).foo(bar);
      super(SuperB).foo();
    }
  }

  C().foo("bar");
  // outputs:
  // SuperA bar
  // SuperB
  ```
