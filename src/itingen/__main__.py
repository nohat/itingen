"""Entry point for python -m itingen execution.

AIDEV-NOTE: Enables running the package directly with `python -m itingen`
instead of requiring the itingen command to be installed.
"""

import sys
from itingen.cli import main

if __name__ == "__main__":
    sys.exit(main())
