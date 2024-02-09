#!/usr/bin/env python
import sys
from pylox.pylox import PyLox

if __name__ == "__main__":
    if len(sys.argv) > 2:
        print("USAGE: ...")
        sys.exit(64)
    pylox = PyLox()
    exit_code = 0
    if len(sys.argv) == 2:
        exit_code = pylox.run_file(sys.argv[1])
    else:
        exit_code = pylox.run_prompt()

    sys.exit(exit_code)
