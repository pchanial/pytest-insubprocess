import pytest


def test_plugin_registration(pytestconfig: pytest.Config) -> None:
    """Test that the plugin is properly registered with pytest"""
    plugin = pytestconfig.pluginmanager.get_plugin('insubprocess')
    assert plugin is not None


def test_marker_registration1(pytester: pytest.Pytester) -> None:
    """Test that the insubprocess marker is properly registered."""
    pytester.makepyfile(
        """
        import pytest

        def test_marker_exists(pytestconfig: pytest.Config):
            markers = pytestconfig.getini("markers")
            assert any(marker.startswith('insubprocess:') for marker in markers)
    """
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_marker_registration2(pytester: pytest.Pytester) -> None:
    result = pytester.runpytest('--markers')
    result.stdout.fnmatch_lines(['*insubprocess: run test in an isolated subprocess*'])
