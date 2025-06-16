# pytest-insubprocess

A pytest plugin for running tests in isolated subprocesses.

## Features

- Run pytest tests in separate subprocesses for better isolation
- Proper handling of test failures and exceptions across process boundaries
- Maintains pytest's output formatting and reporting
- Preserves pytest command-line options in subprocesses

## Installation

You can install `pytest-insubprocess` via pip:

```bash
pip install pytest-insubprocess
```

## Usage

Once installed, the plugin is automatically registered with pytest. To run your tests in subprocesses, use the `--insubprocess` flag:

```bash
pytest --insubprocess
```

### Basic Example

```python
# test_example.py
import os
import pytest

@pytest.mark.insubprocess
def test_isolated():
    print(f"Running in process: {os.getpid()}")
    assert True
```

Run with:
```bash
pytest test_example.py
```

Each test will run in its own subprocess, providing complete isolation.

## Why Use This Plugin?

- **Process Isolation**: Each test runs in a fresh subprocess, preventing side effects between tests
- **Resource Cleanup**: Processes are terminated after each test, ensuring clean state
- **Memory Isolation**: Memory leaks in one test won't affect others
- **System Resource Independence**: Tests that modify system state won't interfere with each other

## Requirements

- Python 3.7 or later
- pytest 7.0 or later

## Development

To contribute to pytest-insubprocess:

1. Clone the repository:
```bash
git clone https://github.com/pchanial/pytest-insubprocess.git
```

2. Create a virtual environment and install development dependencies:
```bash
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -e ".[test]"
```

3. Run the tests:
```bash
pytest tests/
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Links

- PyPI: [pytest-insubprocess](https://pypi.org/project/pytest-insubprocess)
- Source Code: [GitHub](https://github.com/pchanial/pytest-insubprocess)
- Issue Tracker: [GitHub Issues](https://github.com/pchanial/pytest-insubprocess/issues)

## Support

If you are having issues, please let us know by opening an issue on our [issue tracker](https://github.com/pchanial/pytest-insubprocess/issues).
