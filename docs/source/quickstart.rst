Quick Start
===========

This guide will help you get started with QuickUp! in just a few minutes.

Installation
------------

Install QuickUp! using pip:

.. code-block:: bash

   pip install quickup

Authentication
--------------

Log in with ClickUp via your browser:

.. code-block:: bash

   quickup login

This opens ClickUp in your browser. After approving access, your credentials are saved
automatically — no manual token setup needed.

For CI or automation environments, you can instead set an API token directly:

.. code-block:: bash

   export CLICKUP_TOKEN=your_token_here

Basic Usage
-----------

List all tasks from a specific ClickUp list:

.. code-block:: bash

   quickup --team <team_id> --list <list_id>

Use interactive mode to navigate through your workspace hierarchy:

.. code-block:: bash

   quickup -i

List tasks from the current sprint:

.. code-block:: bash

   quickup sprint --team <team_id>

View details of a specific task:

.. code-block:: bash

   quickup task <task_id>

Update a task's status:

.. code-block:: bash

   quickup update <task_id> --status "In Progress"

Next Steps
----------

- Read the :doc:`Installation` guide for detailed installation instructions
- Check the :doc:`commands` reference for all available CLI options
- Explore :doc:`features` to learn about filtering, grouping, and caching
