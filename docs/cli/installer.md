# `python -m installer`

This interface allows you to install one or more wheels into a Python
interpreter.

## Control bytecode generation

By default, the command compiles installed Python modules at optimisation levels
0 and 1. To install a wheel without generating bytecode:

```sh
python -m installer --no-compile-bytecode sampleproject-1.3.1-py2.py3-none-any.whl
```

To compile only at level 2:

```sh
python -m installer --compile-bytecode 2 sampleproject-1.3.1-py2.py3-none-any.whl
```

Repeat the option to select more than one level. These replace the defaults:

```sh
python -m installer --compile-bytecode 0 --compile-bytecode 2 sampleproject-1.3.1-py2.py3-none-any.whl
```

These options control compilation during installation. The Python source files
are still installed, and Python may generate bytecode when they are imported
later. If both flags are supplied, `--no-compile-bytecode` takes precedence.

## Options

```{argparse}
:module: installer.__main__
:func: _get_main_parser
:prog: python -m installer
```
