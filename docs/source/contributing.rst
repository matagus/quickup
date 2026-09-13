Contributing Guide
==================

This guide covers setting up a development environment and contributing to QuickUp!.

Setting Up the Development Environment
--------------------------------------

Clone the repository:

.. code-block:: bash

   git clone https://github.com/matagus/quickup.git
   cd quickup

Install development dependencies:

.. code-block:: bash

   hatch run dev:install

Or using pip:

.. code-block:: bash

   pip install -e ".[dev]"

Running the Test Suite
----------------------

Run all tests:

.. code-block:: bash

   hatch run test:test

Run tests with coverage:

.. code-block:: bash

   hatch run test:cov

This generates coverage reports in:
- ``coverage.json`` - JSON format
- Terminal output - Human-readable summary

Run tests on specific Python versions (3.11-3.14):

.. code-block:: bash

   hatch run +py=3.11 test:test
   hatch run +py=3.12 test:test

Run specific test files or add pytest arguments:

.. code-block:: bash

   hatch run test:test tests/test_cli.py
   hatch run test:test -k test_something

Using Pre-commit
----------------

Install pre-commit hooks:

.. code-block:: bash

   pre-commit install

Run pre-commit on all files:

.. code-block:: bash

   pre-commit run --all-files

Pre-commit hooks run automatically on commits.

Building Documentation
----------------------

Build the HTML documentation:

.. code-block:: bash

   hatch run docs:build

Documentation is output to ``docs/build/``.

Serving Documentation Locally
-----------------------------

Start a local web server to view documentation:

.. code-block:: bash

   hatch run docs:serve

Open http://localhost:8000 in your browser.

Coverage Reports
----------------

Coverage reports show which lines of code are executed during tests.

Generate and view coverage:

.. code-block:: bash

   hatch run test:cov

The ``coverage report`` command displays a summary table showing:
- Statement count per module
- Number of covered/missing statements
- Coverage percentage

Look for modules with low coverage and add tests for uncovered branches.

Development Scripts Reference
-----------------------------

+----------------------------------+-------------------------------------------+
| Command                          | Description                               |
+==================================+===========================================+
| ``hatch run test:test``          | Run pytest test suite                     |
+----------------------------------+-------------------------------------------+
| ``hatch run test:cov``           | Run tests with coverage                   |
+----------------------------------+-------------------------------------------+
| ``hatch run test:cov-report``    | Generate coverage reports                 |
+----------------------------------+-------------------------------------------+
| ``hatch run docs:build``         | Build Sphinx documentation                |
+----------------------------------+-------------------------------------------+
| ``hatch run docs:serve``         | Serve docs on localhost:8000              |
+----------------------------------+-------------------------------------------+
| ``hatch run dev:install``        | Install development dependencies          |
+----------------------------------+-------------------------------------------+
| ``hatch run +py=3.11 test:test`` | Run tests on Python 3.11                  |
+----------------------------------+-------------------------------------------+
