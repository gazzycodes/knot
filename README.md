# knot

[![CI](https://github.com/gazzycodes/knot/actions/workflows/ci.yml/badge.svg)](https://github.com/gazzycodes/knot/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/knot-imports.svg)](https://pypi.org/project/knot-imports/)

**Detect and visualize circular imports in Python projects — fast, static, and dependency-free.**

Circular imports are a common source of `ImportError` and "partially initialized
module" failures, and they quietly couple your code together. `knot` finds them
*without importing or running* a single line of your project: it parses the
source with the standard-library `ast` module, builds the internal module
dependency graph, and reports every cycle with a concrete example path.

It has **zero runtime dependencies**, runs in CI (non-zero exit on cycles), and
can emit a [Mermaid](https://mermaid.js.org/) diagram of your import graph.

## Demo

![knot detecting a circular import in the bundled example project](https://raw.githubusercontent.com/gazzycodes/knot/main/docs/demo.gif)

> The [`examples/shop`](examples/shop) package intentionally contains a circular
> import so you can try `knot` immediately: `knot examples/shop`.

## Installation

```bash
pip install knot-imports
```

Or run from a checkout without installing:

```bash
PYTHONPATH=src python -m knot path/to/project
```

## Usage

```bash
# Analyze the current directory
knot .

# Analyze a specific package or project
knot path/to/your_package

# Exclude directories (repeatable); common ones are skipped by default
knot . --exclude migrations --exclude examples
```

### Example

Given a package where `order` and `customer` import each other:

```text
$ knot shop
Analyzed 3 modules, 3 internal imports.
Found 1 import cycle:

  1. shop.customer -> shop.order -> shop.customer
```

### Output formats

`--format text` (default), `json`, or `mermaid`:

```bash
knot . --format json      # machine-readable: summary, cycles, full graph
knot . --format mermaid   # a graph LR diagram with cycle nodes highlighted
```

The Mermaid output pastes directly into a GitHub Markdown ` ```mermaid ` block
or the [Mermaid Live Editor](https://mermaid.live/).

### Exit codes

| Code | Meaning                     |
|------|-----------------------------|
| `0`  | No cycles found             |
| `1`  | One or more cycles found    |
| `2`  | Error (e.g. path not found) |

Pass `--no-fail` to always exit `0` (useful when you only want the report).
Drop `knot .` into a pre-commit hook or CI step to keep cycles out of `main`.

## How it works

1. **Discover** every `.py` file under the target and map it to its
   fully-qualified module name, mirroring how Python would import it.
2. **Parse** each file with `ast` and resolve `import` / `from ... import`
   statements (absolute *and* relative) to internal modules; external imports
   are ignored.
3. **Detect cycles** by computing strongly connected components with an
   iterative implementation of Tarjan's algorithm (safe on very large graphs),
   then extract a concrete example path for each cycle.

## Development

```bash
git clone https://github.com/gazzycodes/knot
cd knot
PYTHONPATH=src python -m unittest discover -s tests -v
```

The demo GIF is regenerated with `python make_demo.py` (requires `pillow`).

Contributions are welcome — please open an issue or PR.

## License

MIT — see [LICENSE](LICENSE).
