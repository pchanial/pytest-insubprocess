import os
from pathlib import Path

import pytest


def test_same_process_execution(pytester: pytest.Pytester) -> None:
    """Test basic same process execution"""
    pytester.makepyfile("""
        import os
        from pathlib import Path

        def test():
            pid = int(Path('test_same_process_execution.txt').read_text())
            assert os.getpid() == pid
    """)
    pytester.maketxtfile(str(os.getpid()))
    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_subprocess_execution(pytester: pytest.Pytester) -> None:
    """Test basic in the subprocess execution"""
    pytester.makepyfile("""
        import os
        from pathlib import Path
        import pytest

        @pytest.mark.insubprocess
        def test_example():
            pid = int(Path('test_subprocess_execution.txt').read_text())
            assert os.getpid() != pid
            assert os.getppid() == pid
    """)
    pytester.maketxtfile(str(os.getpid()))

    result = pytester.runpytest('-s', '-vv')
    result.assert_outcomes(passed=1)


# run OK
def test_failure_assertion(pytester: pytest.Pytester) -> None:
    """Test subprocess execution with a failing test."""
    pytester.makepyfile("""
        import pytest

        @pytest.mark.insubprocess
        def test_failing():
            assert False, 'This test should fail'
    """)

    result = pytester.runpytest()
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(['*This test should fail*'])


def test_failure_error(pytester: pytest.Pytester) -> None:
    """Test subprocess execution with a test with error."""
    pytester.makepyfile("""
        import pytest

        @pytest.mark.insubprocess
        def test():
            1 / 0
    """)

    result = pytester.runpytest()
    result.assert_outcomes(failed=1)


def test_failure_error_custom(pytester: pytest.Pytester) -> None:
    """Test subprocess execution with a test with error."""
    pytester.makepyfile("""
        import pytest
        import xmltodict

        @pytest.mark.insubprocess
        def test():
            raise xmltodict.expat.ExpatError('This test should error')
    """)

    result = pytester.runpytest()
    result.assert_outcomes(failed=1)


@pytest.mark.xfail(reason='setup errors are propagated as test failures, not errors.')
def test_error_setup(pytester: pytest.Pytester) -> None:
    """Test subprocess execution with a setup error."""
    pytester.makepyfile("""
        import pytest
        @pytest.fixture
        def error():
            1 / 0

        @pytest.mark.insubprocess
        def test(error):
            pass
    """)
    result = pytester.runpytest()
    result.assert_outcomes(errors=1)
    result.stdout.fnmatch_lines(['*ZeroDivisionError*'])


@pytest.mark.xfail(reason='teardown errors are propagated as test failures, not errors.')
def test_error_teardown(pytester: pytest.Pytester) -> None:
    """Test subprocess execution with a teardown error."""
    pytester.makepyfile(
        """
        import pytest

        @pytest.fixture
        def error():
            yield
            1 / 0

        @pytest.mark.insubprocess
        def test(error):
            pass
    """
    )
    result = pytester.runpytest()
    result.assert_outcomes(errors=1)


def test_skip1(pytester: pytest.Pytester) -> None:
    """Test subprocess execution with a skipped test."""
    pytester.makepyfile("""
        import pytest

        @pytest.mark.insubprocess
        def test():
            pytest.skip('This test should be skipped')
    """)

    result = pytester.runpytest('-v')
    result.assert_outcomes(skipped=1)
    result.stdout.fnmatch_lines(['*This test should be skipped*'])


def test_skip2(pytester: pytest.Pytester) -> None:
    """Test subprocess execution with a skipped test."""
    pytester.makepyfile("""
        import pytest

        @pytest.mark.skip(reason='This test should be skipped')
        @pytest.mark.insubprocess
        def test_failing():
            pass
    """)

    result = pytester.runpytest('-v')
    result.assert_outcomes(skipped=1)
    result.stdout.fnmatch_lines(['*This test should be skipped*'])


def test_xfail_assertion(pytester: pytest.Pytester) -> None:
    """Test subprocess execution of a XFAIL test with assertion in test body,."""
    pytester.makepyfile("""
        import pytest

        @pytest.mark.xfail(reason='This test should xfail')
        @pytest.mark.insubprocess
        def test():
            assert False
    """)

    result = pytester.runpytest('-v')
    result.assert_outcomes(xfailed=1)
    result.stdout.fnmatch_lines(['*This test should xfail*'])


def test_xfail2(pytester: pytest.Pytester) -> None:
    """Test subprocess execution of a XFAIL test with error in test body."""
    pytester.makepyfile("""
        import pytest

        @pytest.mark.xfail(reason='This test should xfail')
        @pytest.mark.insubprocess
        def test():
            1 / 0
    """)

    result = pytester.runpytest('-v')
    result.assert_outcomes(xfailed=1)
    result.stdout.fnmatch_lines(['*This test should xfail*'])


def test_xfail3(pytester: pytest.Pytester) -> None:
    """Test subprocess execution of a test with pytest.xfail() call in test body."""
    pytester.makepyfile("""
        import pytest

        @pytest.mark.insubprocess
        def test():
            pytest.xfail('This test should xfail')
    """)
    result = pytester.runpytest('-vv')
    result.assert_outcomes(xfailed=1)
    result.stdout.fnmatch_lines(['*This test should xfail*'])


def test_xpass(pytester: pytest.Pytester) -> None:
    """Test subprocess execution of an xpassed test."""
    pytester.makepyfile("""
        import pytest

        @pytest.mark.xfail(reason='This test should xfail')
        @pytest.mark.insubprocess
        def test():
            assert True
    """)

    result = pytester.runpytest()
    result.assert_outcomes(xpassed=1)


def test_many_executions(pytester: pytest.Pytester) -> None:
    """Test subprocess execution with a failing test."""
    pytester.makepyfile("""
        import pytest

        @pytest.mark.insubprocess
        def test1():
            pass

        @pytest.mark.insubprocess
        @pytest.mark.parametrize('value', [1, 2, 3])
        def test2(value: int):
            pass

        @pytest.mark.insubprocess
        def test_failing1():
            assert False, 'This test should fail'

        @pytest.mark.insubprocess
        @pytest.mark.parametrize('value', [1, 2, 3])
        def test_failing2(value: int):
            assert False, 'This test should fail'
    """)

    result = pytester.runpytest()
    result.assert_outcomes(passed=4, failed=4)
    result.stdout.fnmatch_lines(['*This test should fail*'])


# run OK
def test_multiple_tests_in_subprocess(pytester: pytest.Pytester) -> None:
    """Test that tests run in separate processes"""
    pytester.makepyfile("""
        import os
        from pathlib import Path
        import pytest

        @pytest.mark.insubprocess
        def test_get_pid1():
            pid = os.getpid()
            Path('pid1.txt').write_text(str(pid))

        @pytest.mark.insubprocess
        def test_get_pid2():
            pid = os.getpid()
            Path('pid2.txt').write_text(str(pid))
    """)

    result = pytester.runpytest()
    result.assert_outcomes(passed=2)
    pid1 = int(Path('pid1.txt').read_text())
    pid2 = int(Path('pid2.txt').read_text())
    assert pid1 != pid2


def test_memory_isolation(pytester: pytest.Pytester) -> None:
    """Test memory isolation between subprocess tests"""
    pytester.makepyfile("""
        import pytest

        _global_var = []

        @pytest.mark.insubprocess
        def test_modify_global():
            global _global_var
            _global_var.append("data")
            assert len(_global_var) == 1

        @pytest.mark.insubprocess
        def test_clean_global():
            global _global_var
            # Should start clean in new subprocess
            assert len(_global_var) == 0
    """)

    result = pytester.runpytest()
    result.assert_outcomes(passed=2)


def test_environment_isolation(pytester: pytest.Pytester) -> None:
    """Test environment variable isolation"""
    pytester.makepyfile("""
        import os
        import pytest

        @pytest.mark.insubprocess
        def test_set_env():
            os.environ['SUBPROCESS_TEST'] = 'value1'
            assert os.environ['SUBPROCESS_TEST'] == 'value1'

        @pytest.mark.insubprocess
        def test_clean_env():
            # Should not see env var from previous test
            assert 'SUBPROCESS_TEST' not in os.environ
    """)

    result = pytester.runpytest()
    result.assert_outcomes(passed=2)


# Exception Handling Tests
def test_custom_exception_handling(pytester: pytest.Pytester) -> None:
    """Test that custom exceptions are properly propagated"""
    pytester.makepyfile("""
        import pytest

        class CustomError(Exception):
            pass

        @pytest.mark.insubprocess
        def test_custom_exception():
            raise CustomError("Custom error message")
    """)

    result = pytester.runpytest()
    result.assert_outcomes(failed=1)
    assert 'CustomError' in result.stdout.str()
    assert 'Custom error message' in result.stdout.str()


def test_import_error_handling(pytester: pytest.Pytester) -> None:
    """Test import errors in the subprocess"""
    pytester.makepyfile("""
        import nonexistent_module

        @pytest.mark.insubprocess
        def test_import():
            assert True
    """)

    result = pytester.runpytest()
    result.assert_outcomes(errors=1)
    assert 'ModuleNotFoundError' in result.stdout.str()


def test_syntax_error_handling(pytester: pytest.Pytester) -> None:
    """Test syntax errors in the subprocess"""
    pytester.makepyfile("""
        import pytest

        @pytest.mark.insubprocess
        def test_syntax(
            # Missing closing parenthesis
            assert True
    """)

    result = pytester.runpytest()
    result.assert_outcomes(errors=1)


# Command Line Options Tests
def test_option_verbose(pytester: pytest.Pytester) -> None:
    """Test that the verbose option is forwarded to the subprocess"""
    pytester.makepyfile("""
        import pytest

        @pytest.mark.insubprocess
        def test_verbose():
            assert True
    """)

    result = pytester.runpytest('-v')
    assert 'PASSED' in str(result.stdout)


def test_option_quiet(pytester: pytest.Pytester) -> None:
    """Test that the quiet option is forwarded to the subprocess"""
    pytester.makepyfile("""
        import pytest

        @pytest.mark.insubprocess
        def test_quiet():
            assert True
    """)

    result = pytester.runpytest('-q')
    assert 'PASSED' not in str(result.stdout)


def test_option_capture_no(pytester: pytest.Pytester) -> None:
    """Test output capture in the subprocess"""
    pytester.makepyfile("""
        import pytest

        @pytest.mark.insubprocess
        def test_with_output():
            print("Test output")
            assert True
    """)

    result = pytester.runpytest('--capture=no')
    result.assert_outcomes(passed=1)
    assert 'Test output' in str(result.stdout)


def test_option_capture_fd(pytester: pytest.Pytester) -> None:
    """Test output capture in the subprocess"""
    pytester.makepyfile("""
        import pytest

        @pytest.mark.insubprocess
        def test_with_output():
            print("Test output fd")
            assert True
    """)

    result = pytester.runpytest('--capture=fd')
    result.assert_outcomes(passed=1)
    assert 'Test output fd' not in str(result.stdout)


def test_option_traceback(pytester: pytest.Pytester) -> None:
    """Test traceback options in the subprocess"""
    pytester.makepyfile("""
        import pytest

        @pytest.mark.insubprocess
        def test_with_traceback():
            assert False, "Test failure for traceback"
    """)

    result = pytester.runpytest('--tb=short')
    result.assert_outcomes(failed=1)
    assert 'Test failure for traceback' in result.stdout.str()


# Configuration Tests
def test_conftest_loading(pytester: pytest.Pytester) -> None:
    """Test that conftest.py is loaded in the subprocess"""
    pytester.makeconftest("""
        import pytest

        @pytest.fixture
        def custom_fixture():
            return "custom_value"
    """)

    pytester.makepyfile("""
        def test_fixture_available(custom_fixture):
            assert custom_fixture == "custom_value"
    """)

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


# Integration Tests
def test_fixture_loading(pytester: pytest.Pytester) -> None:
    """Test that pytest fixtures work in the subprocess"""
    pytester.makepyfile("""
        import pytest

        @pytest.fixture
        def sample_data():
            return [1, 2, 3, 4, 5]

        def test_fixture_usage(sample_data):
            assert len(sample_data) == 5
            assert sum(sample_data) == 15
    """)

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_module_level_fixtures(pytester: pytest.Pytester) -> None:
    """Test module-level fixtures in the subprocess"""
    pytester.makepyfile("""
        import pytest

        @pytest.fixture(scope="module")
        def module_fixture():
            return "module_value"

        def test_module_fixture_1(module_fixture):
            assert module_fixture == "module_value"

        def test_module_fixture_2(module_fixture):
            assert module_fixture == "module_value"
    """)

    result = pytester.runpytest()
    result.assert_outcomes(passed=2)


def test_setup_teardown_functions(pytester: pytest.Pytester) -> None:
    """Test setup/teardown functions in the subprocess"""
    pytester.makepyfile("""
        import pytest

        test_state = {"setup": False, "teardown": False}

        def setup_function():
            test_state["setup"] = True

        def teardown_function():
            test_state["teardown"] = True

        @pytest.mark.insubprocess
        def test_setup_called():
            assert test_state["setup"] is True
    """)

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_pytest_markers(pytester: pytest.Pytester) -> None:
    """Test that pytest markers work in the subprocess"""
    pytester.makepyfile("""
        import pytest

        @pytest.mark.insubprocess
        @pytest.mark.slow
        def test_marked():
            assert True

        @pytest.mark.insubprocess
        def test_unmarked():
            assert True
    """)

    result = pytester.runpytest('-m', 'slow')
    result.assert_outcomes(passed=1)


def test_parametrized_tests(pytester: pytest.Pytester) -> None:
    """Test parametrized tests in the subprocess"""
    pytester.makepyfile("""
        import pytest

        @pytest.mark.insubprocess
        @pytest.mark.parametrize("value", [1, 2, 3])
        def test_parametrize(value):
            assert value > 0
    """)

    result = pytester.runpytest()
    result.assert_outcomes(passed=3)


# Performance Tests
def test_multiple_test_files(pytester: pytest.Pytester) -> None:
    """Test running multiple test files in the subprocesses"""
    pytester.makepyfile(
        test_file1="""
        import pytest

        @pytest.mark.insubprocess
        def test_file1_func1():
            assert True

        @pytest.mark.insubprocess
        def test_file1_func2():
            assert True
    """
    )

    pytester.makepyfile(
        test_file2="""
        import pytest

        @pytest.mark.insubprocess
        def test_file2_func1():
            assert True

        @pytest.mark.insubprocess
        def test_file2_func2():
            assert True
    """
    )

    result = pytester.runpytest()
    result.assert_outcomes(passed=4)


def test_no_tests_found(pytester: pytest.Pytester) -> None:
    """Test handling when no tests are found"""
    pytester.makepyfile("""
        def regular_function():
            return True
    """)

    result = pytester.runpytest()
    assert 'no tests ran' in result.stdout.str().lower()


def test_class_based_tests1(pytester: pytest.Pytester) -> None:
    """Class-based tests in the subprocess"""
    pytester.makepyfile("""
        import pytest

        class TestClass:
            @pytest.mark.insubprocess
            def test_method1(self):
                assert True

            def test_method2(self):
                assert 1 + 1 == 2
    """)

    result = pytester.runpytest()
    result.assert_outcomes(passed=2)


def test_class_based_tests2(pytester: pytest.Pytester) -> None:
    """Class-based tests in the subprocess"""
    pytester.makepyfile("""
        import pytest

        @pytest.mark.insubprocess
        class TestClass:
            def test_method1(self):
                assert True

            def test_method2(self):
                assert 1 + 1 == 2
    """)

    result = pytester.runpytest()
    result.assert_outcomes(passed=2)


def test_fixture_capsys(pytester: pytest.Pytester) -> None:
    """Test that capsys fixture works in the subprocess"""
    pytester.makepyfile("""
        import pytest

        @pytest.mark.insubprocess
        def test_capsys(capsys):
            print("hello")
            captured = capsys.readouterr()
            assert captured.out == "hello\\n"
    """)

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)
