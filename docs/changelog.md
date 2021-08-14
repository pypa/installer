# Changelog

## v0.2.3 (Jul 29, 2021)

- Fix entry point handling in {any}`installer.install`.

## v0.2.2 (May 15, 2021)

- Teach {any}`SchemeDictionaryDestination` to create subfolders.

## v0.2.1 (May 15, 2021)

- Change {any}`parse_record_file` to yield the elements as a tuple, instead of
  {any}`RecordEntry` objects.
- Implement {any}`WheelFile`, completing the end-to-end wheel installation
  pipeline.
- Generate {any}`RecordEntry` for `RECORD` file in the
  {any}`installer.install`, instead of requiring every `WheelDestination`
  implementation to do the exact same thing.

## v0.2.0 (May 3, 2021)

- Initial release.

---

Thank you to [Dan Ryan] and [Tzu-ping Chung] for the project name on
PyPI. The PyPI releases before 0.2.0 come from
<https://github.com/sarugaku/installer> and have been [yanked].

[dan ryan]: https://github.com/techalchemy
[tzu-ping chung]: https://github.com/uranusjr
[yanked]: https://www.python.org/dev/peps/pep-0592/#abstract
