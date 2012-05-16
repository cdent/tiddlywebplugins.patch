


def test_compile():
    try:
        import tiddlywebplugins.patch
        assert True
    except ImportError, exc:
        assert False, exc
