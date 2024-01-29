import sys
from pylox.pylox import PyLox

if __name__ == "__main__":
    if len(sys.argv) > 2:
        print("USAGE: ...")
        sys.exit(64)
    pylox = PyLox()
    if (len(sys.argv) == 2):
        pylox.run_file(sys.argv[1])
    else:
        pylox.run_prompt()
