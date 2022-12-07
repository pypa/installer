# Changelog

## v0.6.0 (Dec 7, 2022)

- Add support for Python 3.11 (#154)
- Encode hashes in `RECORD` files correctly (#141)
- Add `py.typed` marker file (#138)
- Implement `--prefix` option (#103)
- Fix the unbound `is_executable` (#115)
- Construct `RECORD` file using `csv.writer` (#118)
- Move away from `import installer.xyz` style imports (#110)
- Improve existing documentation content (typos, formatting) (#109)

## v0.5.1 (Mar 11, 2022)

- Change all names in `installer.__main__` to be underscore prefixed.
- Update project URL after move to the `pypa` organisation.
- Rewrite imports to be compatible with `vendoring`.

## v0.5.0 (Feb 16, 2022)

- Add a CLI, to install a wheel into the currently-running Python.
- Convert Windows paths to `/` separated when writing `RECORD`.
- Drop support for Python 3.6 and lower.
- Preserve the executable bit from wheels being installed.
- Write records in `RECORD` with relative paths.
- Improve API documentation.

## v0.4.0 (Oct 13, 2021)

- Pass schemes into {any}`WheelDestination.finalize_installation`.

## v0.3.0 (Oct 11, 2021)

- Add support for ARM 64 executables on Windows.
- Improve handling of wheels that contain entries for directories.

## v0.2.3 (Jul 29, 2021)

- Fix entry point handling in {any}`installer.install`.

## v0.2.2 (May 15, 2021)

- Teach {any}`SchemeDictionaryDestination` to create subfolders.

## v0.2.1 (May 15, 2021)

- Change {any}`parse_record_file` to yield the elements as a tuple, instead of
  {any}`RecordEntry` objects.
- Implement {any}`WheelFile`, completing the end-to-end wheel installation
  pipeline.
- Generate {any}`RecordEntry` for `RECORD` file in the {any}`installer.install`,
  instead of requiring every `WheelDestination` implementation to do the exact
  same thing.

## v0.2.0 (May 3, 2021)

- Initial release.

---

Thank you to [Dan Ryan] and [Tzu-ping Chung] for the project name on PyPI. The
PyPI releases before 0.2.0 come from <https://github.com/sarugaku/installer> and
have been [yanked].

[dan ryan]: https://github.com/techalchemy
[tzu-ping chung]: https://github.com/uranusjr
[yanked]: https://www.python.org/dev/peps/pep-0592/#abstract
