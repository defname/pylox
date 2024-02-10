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

builtin functions:
- `time()` returns number of miliseconds since epoch
- `input()` reads line from stdin and returns it
- `type(x)` returns the type of x ("string", "number", "fun", "class", "instance")
- `isinstance(x, cls)` returns true if x is an instance of cls or if cls is a superclass of the class of x
- `hasprop(obj, prop)` returns true if x has property `prop`
- `tostring(x, n)` returns the string representation of x. if x and n are numbers x is formatted with floor(n) decimals
- `tonumber(x)` if x is a string with a valid number it is returned as number, otherwise nil is returned
- `round(x, n)` round x to floor(n) decimals. return nil if x or n is not a number.
- `floor(x)` returns biggest integer smaller or equal to x or nil if x is not a number
- `include(filename)` reads the specified file and runs it in the interpeter
