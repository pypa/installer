from installer.__main__ import get_scheme_dict, main

def test_get_scheme_dict():
    d = get_scheme_dict(distribution_name='foo')
    assert set(d.keys()) >= {'purelib', 'platlib', 'headers', 'scripts', 'data'}


def test_main(fancy_wheel, tmp_path):
    destdir = tmp_path / 'dest'

    main([str(fancy_wheel), '-d', str(destdir)], "python -m installer")

    installed_py_files = destdir.rglob('*.py')

    assert {f.stem for f in installed_py_files} == {'__init__', '__main__', 'data'}

    installed_pyc_files = destdir.rglob('*.pyc')
    assert {f.name.split('.')[0] for f in installed_pyc_files} == {
        '__init__', '__main__'
    }

def test_main_no_pyc(fancy_wheel, tmp_path):
    destdir = tmp_path / 'dest'

    main([str(fancy_wheel), '-d', str(destdir), '--no-compile-bytecode'], "python -m installer")

    installed_py_files = destdir.rglob('*.py')

    assert {f.stem for f in installed_py_files} == {'__init__', '__main__', 'data'}

    installed_pyc_files = destdir.rglob('*.pyc')
    assert set(installed_pyc_files) == set()
