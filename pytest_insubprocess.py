import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Literal, cast
from xml.parsers.expat import ExpatError

import pytest
import xmltodict
from _pytest.reports import TestReport


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line('markers', 'insubprocess: run test in an isolated subprocess')


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_protocol(item: pytest.Item, nextitem: pytest.Item | None) -> object | None:
    # Check if the test should be executed in a subprocess
    insubprocess = item.get_closest_marker('insubprocess')
    if not insubprocess or os.environ.get('_PYTEST_INSUBPROCESS') == '1':
        return None  # Normal handling

    item.session._setupstate.teardown_exact(nextitem)

    # Temporary directory for the JUnit XML report
    with tempfile.TemporaryDirectory() as tmpdir:
        junit_xml_path = Path(tmpdir) / 'results.xml'

        # Execute the test in a subprocess using its nodeid
        cmd = [
            sys.executable,
            '-m',
            'pytest',
            '--capture=fd',
            '-o',
            'junit_logging=all',
            '--junitxml=' + junit_xml_path.as_posix(),
            item.nodeid,
        ] + _get_options(item.config)
        env = os.environ | {'_PYTEST_INSUBPROCESS': '1'}
        _ = subprocess.run(
            cmd,
            capture_output=True,
            encoding='utf-8',
            check=False,
            env=env,
        )

        # Parse the generated JUnit XML report
        try:
            junit_xml = junit_xml_path.read_text()
        except FileNotFoundError:
            return _create_error_report(item, 'Could not find the junit XML file.')

    report = _parse_junit_xml(item, junit_xml)
    item.ihook.pytest_runtest_logreport(report=report)
    return True


def _get_options(config: pytest.Config) -> list[str]:
    cmd = []
    if (quiet := config.getoption('--quiet')) > 0:
        cmd.append('-' + quiet * 'q')
    if (verbose := config.getoption('--verbose')) > 0:
        cmd.append('-' + verbose * 'v')
    return cmd


def _parse_junit_xml(item: pytest.Item, junit_xml: str) -> TestReport:
    try:
        root = xmltodict.parse(junit_xml)
    except ExpatError:
        # Parsing error
        return _create_error_report(item, 'Error when parsing the subprocess test report.')

    try:
        testcase = _find_testcase(root)
    except ValueError:
        return _create_error_report(item, 'Test not found in the subprocess report.')

    outcome, longrepr, type_ = _parse_testcase_outcome(item, testcase)

    when: Literal['setup', 'call', 'teardown']
    if isinstance(longrepr, str) and longrepr.startswith('failed on setup'):
        when = 'setup'
    elif isinstance(longrepr, str) and longrepr.startswith('failed on teardown'):
        when = 'teardown'
    else:
        when = 'call'

    duration = float(testcase['@time'])
    system_out = testcase['system-out']
    system_err = testcase['system-err']

    capture = item.config.getoption('--capture')
    if capture in ['no', 'tee-sys']:
        print(system_out)

    # Create the test report
    report = TestReport(
        nodeid=item.nodeid,
        location=item.location,
        keywords=item.keywords,
        outcome=outcome,
        longrepr=longrepr,
        when=when,
        duration=duration,
        sections=[
            ('Captured stdout', system_out),
            ('Captured stderr', system_err),
        ],
    )

    xfail_marker = item.get_closest_marker('xfail')
    if outcome == 'skipped' and type_ == 'pytest.xfail':
        if xfail_marker is not None:
            reason = xfail_marker.kwargs['reason']
        else:
            assert isinstance(longrepr, tuple)
            reason = longrepr[2]
        report.wasxfail = f'reason: {reason}'
    elif outcome == 'passed' and xfail_marker is not None:
        reason = xfail_marker.kwargs['reason']
        report.wasxfail = f'reason: {reason}'

    return report


def _find_testcase(root: dict[str, Any]) -> dict[str, Any]:
    """Find the testcase element in the XML tree."""
    element = root.get('testsuites')
    if element is None:
        raise ValueError('No testsuites element in the XML tree.')
    element = element.get('testsuite')
    if element is None:
        raise ValueError('No testsuite element in the XML tree.')
    element = element.get('testcase')
    if element is None:
        raise ValueError('No testcase element in the XML tree.')
    if not isinstance(element, dict):
        raise ValueError('The testcase element is not a dictionary.')
    return cast(dict[str, Any], element)


def _parse_testcase_outcome(
    item: pytest.Item,
    testcase: dict[str, Any],
) -> tuple[Literal['failed', 'passed', 'skipped'], str | tuple[str, int, str] | None, str | None]:
    """Return the outcome of the testcase and its longrepr, if any, in the XML tree."""
    if (failure := testcase.get('failure')) is not None:
        return 'failed', failure['@message'], None
    if (skipped := testcase.get('skipped')) is not None:
        path, line = item.reportinfo()[:2]
        assert line is not None
        longrepr = str(path), line, cast(str, skipped['@message'])
        return 'skipped', longrepr, skipped['@type']
    return 'passed', None, None


def _create_error_report(item: pytest.Item, message: str) -> pytest.TestReport:
    """Crée un rapport d'erreur pour les cas exceptionnels."""
    return TestReport(
        nodeid=item.nodeid,
        location=item.location,
        keywords=item.keywords,
        outcome='failed',
        longrepr=message,
        when='call',
        duration=0.0,
        sections=[],
    )
