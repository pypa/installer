# Contributing

Thank you for your interest in contributing to installer. We welcome all
contributions and greatly appreciate your effort!

## Code of Conduct

Everyone interacting in the pip project's codebases, issue trackers, chat rooms,
and mailing lists is expected to follow the [PyPA Code of Conduct][coc].

[coc]: https://www.pypa.io/en/latest/code-of-conduct/

## Bugs and Feature Requests

If you have found any bugs or would like to request a new feature, please do
check if there is an existing issue already filed for the same, in the
project's GitHub [issue tracker]. If not, please file a new issue.

If you want to help out by fixing bugs, choose an open issue in the [issue
tracker] to work on and claim it by posting a comment saying "I would like to
work on this.". Feel free to ask any doubts in the issue thread.

While working on implementing the feature, please go ahead and file a pull
request. Filing a pull request early allows for getting feedback as early as
possible.

[issue tracker]: https://github.com/pradyunsg/installer/issues

## Pull Requests

Pull Requests should be small to facilitate easier review. Keep them
self-contained, and limited in scope. Studies have shown that review quality
falls off as patch size grows. Sometimes this will result in many small PRs to
land a single large feature.

Checklist:

1. All pull requests *must* be made against the `master` branch.
2. Include tests for any functionality you implement. Any contributions helping
   improve existing tests are welcome.
3. Update documentation as necessary and provide documentation for any new
   functionality.

## Development

[nox] is used to simplify invocation and usage of all the tooling used during
development.

[nox]: https://github.com/theacodes/nox

### Code Convention

This codebase uses the following tools for enforcing a code convention:

- [black] for code formatting
- [isort] for import sorting
- [mypy] for static type checking
- [pre-commit] for managing all the linters

To run all the linters:

```sh-session
$ nox -s lint
```

[black]: https://github.com/psf/black
[isort]: https://github.com/timothycrosley/isort
[mypy]: https://github.com/python/mypy
[pre-commit]: https://pre-commit.com/

### Testing

This codebase uses [pytest] as the testing framework and [coverage] for
generating code coverage metrics. We enforce a strict 100% test coverage policy
for all code contributions, although [code coverage isn't everything].

To run all the tests:

```sh-session
$ nox -s test
```

nox has been configured to forward any additional arguments it is given to
pytest. This enables the use of [pytest's rich CLI].

```
$ # Using file name
$ nox -s test -- tests/*.py
$ # Using markers
$ nox -s test -- -m unit
$ # Using keywords
$ nox -s test -- -k "basic"
```

[pytest]: https://docs.pytest.org/en/stable/
[coverage]: https://coverage.readthedocs.io/
[code coverage isn't everything]: https://bryanpendleton.blogspot.com/2011/02/code-coverage-isnt-everything-but-its.html
[pytest's rich CLI]: https://docs.pytest.org/en/latest/usage.html#specifying-tests-selecting-tests

### Documentation

This codebase uses [Sphinx] for generating documentation.

To build the documentation:

```sh-session
$ nox -s docs
```

[Sphinx]: https://www.sphinx-doc.org/
