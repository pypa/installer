# Design and Scope

## What this is for

This project is born out of [this discussion][1]. Effectively, the volunteers
who maintain the Python Packaging toolchain identified a need for a library in
the ecology that handles the details of "wheel -> installed package". This is
that library.

There's also a need for “a fast tool to populate a package into an environment”
and this library can be used to build that. This package itself might also
"grow" a CLI, to provide just that functionality.

[1]: https://discuss.python.org/t/3869/

## What is provided

- Abstractions for installation of a wheel distribution.
- Utilities for writing concrete implementations of these abstractions.
- Concrete implementations of these abstraction, for the most common usecase.
- Utilities for handling wheel RECORD files.
- Utilities for generating Python script launchers.
