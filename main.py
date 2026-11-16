"""PIM entry point.

Usage:
    python main.py [--debug]
"""

import sys

from controller import AppController
from model import PIMRepository
from view import ConsoleView


def build_app(debug=False):
    """Create the application with its three layers connected."""
    return AppController(repository=PIMRepository(), view=ConsoleView(), debug=debug)


def parse_args(argv):
    """Return (debug, unknown) for the given command line arguments."""
    debug = False
    unknown = []

    for argument in argv:
        if argument == "--debug":
            debug = True
        else:
            unknown.append(argument)

    return debug, unknown


def main():
    """Run the application. Returns the process exit code."""
    debug, unknown = parse_args(sys.argv[1:])

    if unknown:
        print(f"unknown argument(s): {' '.join(unknown)}", file=sys.stderr)
        print("usage: python main.py [--debug]", file=sys.stderr)
        return 2

    app = build_app(debug=debug)

    try:
        app.run()
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
