"""Allow running the package with ``python -m knot``."""

from knot.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
