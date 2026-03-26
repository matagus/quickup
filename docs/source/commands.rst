Commands Reference
==================

This page documents all available QuickUp! CLI commands and their options.

``quickup login`` - Authenticate
---------------------------------

Authenticate with ClickUp via OAuth. Opens your default browser and waits for the callback.

Synopsis
~~~~~~~~

.. code-block:: bash

   quickup login

Description
~~~~~~~~~~~

Opens the ClickUp authorization page in your browser and starts a local HTTP server on
``localhost:4242`` to receive the OAuth callback. After you approve access in the browser,
the token is exchanged and saved securely to ``~/.quickup/auth.json`` (permissions:
``0o600``). The callback times out after 120 seconds if not completed.

To use a custom OAuth application, set ``QUICKUP_CLIENT_ID`` and ``QUICKUP_CLIENT_SECRET``
environment variables before running ``quickup login``.

Examples
~~~~~~~~

Log in with the default QuickUp! OAuth application:

.. code-block:: bash

   quickup login

``quickup logout`` - Remove Stored Credentials
-----------------------------------------------

Remove the stored OAuth token from disk.

Synopsis
~~~~~~~~

.. code-block:: bash

   quickup logout

Description
~~~~~~~~~~~

Deletes ``~/.quickup/auth.json``. This only removes the OAuth token — tokens set via the
``CLICKUP_TOKEN`` environment variable or a ``.env`` file are not affected.

Examples
~~~~~~~~

.. code-block:: bash

   quickup logout

``quickup`` (default) - List Tasks
----------------------------------

List all tasks from a ClickUp list, grouped by status.

Synopsis
~~~~~~~~

.. code-block:: bash

   quickup [OPTIONS]

Options
~~~~~~~

.. option:: --team

   Team ID (required when multiple teams exist)

.. option:: --space

   Space ID

.. option:: --project

   Project ID

.. option:: --list

   List ID

.. option:: --assignee

   Filter by assignee username (case-insensitive)

.. option:: --priority

   Filter by priority (low, normal, high, urgent)

.. option:: --due-before

   Filter tasks due before date (YYYY-MM-DD)

.. option:: --group-by

   Group by status (default), assignee, or priority

.. option:: --no-cache

   Bypass cache and fetch from API

.. option:: -i, --interactive

   Enable interactive mode for Team/Space/Project/List selection

Examples
~~~~~~~~

Basic usage:

.. code-block:: bash

   quickup --team 12345 --list 67890

Filter by assignee and priority:

.. code-block:: bash

   quickup --team 12345 --list 67890 --assignee john --priority high

Group by assignee:

.. code-block:: bash

   quickup --team 12345 --list 67890 --group-by assignee

Interactive mode:

.. code-block:: bash

   quickup -i

Bypass cache:

.. code-block:: bash

   quickup --team 12345 --list 67890 --no-cache

``quickup sprint`` - Current Sprint Tasks
-----------------------------------------

Auto-detects the current sprint list by searching for lists containing "sprint" or "iteration" in the name.

Synopsis
~~~~~~~~

.. code-block:: bash

   quickup sprint [OPTIONS]

Options
~~~~~~~

Same options as ``quickup`` command, except ``--list`` is not needed (auto-detected).

Examples
~~~~~~~~

List tasks from current sprint:

.. code-block:: bash

   quickup sprint --team 12345

Filter sprint tasks by assignee:

.. code-block:: bash

   quickup sprint --team 12345 --assignee jane

Group sprint tasks by priority:

.. code-block:: bash

   quickup sprint --team 12345 --group-by priority

``quickup task`` - Task Details
-------------------------------

Show detailed information about a specific task.

Synopsis
~~~~~~~~

.. code-block:: bash

   quickup task <task_id> [OPTIONS]

Arguments
~~~~~~~~~

.. option:: task_id

   ClickUp task ID

Options
~~~~~~~

.. option:: --team

   Team ID (required if multiple teams exist)

.. option:: --comments

   Fetch and display task comments

.. option:: -i, --interactive

   Enable interactive mode

Examples
~~~~~~~~

Show task details:

.. code-block:: bash

   quickup task 123456

With team specification:

.. code-block:: bash

   quickup task 123456 --team 12345

Include comments:

.. code-block:: bash

   quickup task 123456 --comments

``quickup update`` - Update Task Status
---------------------------------------

Update the status of a specific task.

Synopsis
~~~~~~~~

.. code-block:: bash

   quickup update <task_id> [OPTIONS]

Arguments
~~~~~~~~~

.. option:: task_id

   ClickUp task ID

Options
~~~~~~~

.. option:: --status

   New status name (e.g., "To Do", "In Progress", "Done")

.. option:: --team

   Team ID (required if multiple teams exist)

.. option:: -i, --interactive

   Enable interactive mode

Examples
~~~~~~~~

Update task status:

.. code-block:: bash

   quickup update 123456 --status "In Progress"

With team specification:

.. code-block:: bash

   quickup update 123456 --status "Done" --team 12345

``quickup comment`` - Post a Comment
-------------------------------------

Post a comment on a specific task. Provide text via ``--text`` or pipe from stdin.

Synopsis
~~~~~~~~

.. code-block:: bash

   quickup comment <task_id> [OPTIONS]

Arguments
~~~~~~~~~

.. option:: task_id

   ClickUp task ID

Options
~~~~~~~

.. option:: --text

   Comment text to post. If omitted, reads from stdin.

.. option:: --notify-all

   Notify all task watchers (default: false)

Examples
~~~~~~~~

Post a comment:

.. code-block:: bash

   quickup comment 123456 --text "This looks good, merging now"

Notify all watchers:

.. code-block:: bash

   quickup comment 123456 --text "Attention everyone" --notify-all

Pipe comment from stdin:

.. code-block:: bash

   echo "Comment from a script" | quickup comment 123456
