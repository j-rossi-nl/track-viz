So you want to participate..
=============================

Pre-Requisites
--------------

On your computer, you need to install:

- Python 3.8
- Poetry_
- Nox_
- nox-poetry_

Refer to the instructions that correspond to your OS.


Clone the Repository
--------------------

Fork the repository (use the fork button on `Source Code`_) and then clone the forked repository.

Either from command-line:

.. code:: console

    $ git clone https://github.com/<your_username>/track-viz.git
    $ git remote add upstream https://github.com/JulienMBABD/track-viz.git

or from the IDE you are using (Pycharm, VSCode, ...).

Set up Development Environment
------------------------------

Use the command line to install all needed packages for development:

.. code:: console

    $ cd track-viz
    $ poetry install

This will create a new virtual Python environment that will include:

- Python 3.8
- ``nox``, ``poetry``
- All dependencies (``pandas``, etc...) of the module
- All development tools (``ipython``, ``jupyter-lab``, ``black``, ...)
- The module ``track-viz`` itself, in editable mode

Note the name of the virtual environment (something like ``track-viz-xxxxxxxx-py3.8``).

Register in your IDE project the corresponding Python executable as the Python interpreter.

Enter the virtual environment:

.. code:: console

    $ poetry shell

Starting from now, the virtual environment is active. Any change done to the source code of the module will be
immediatly available in the shell.

Call the module with:

.. code:: console

    $ track-viz gpx-to-csv --gpx <file> --to <csvfile>

Any change on the source code is immediatly applied and can be observed by launching a command similar to the previous one.

For the list of commands, refer to `Usage <https://track-viz.readthedocs.io/en/latest/usage.html>`_

Install the pre-commit hooks (more on this later):

.. code:: console

    $ pre-commit install


.. _Poetry: https://python-poetry.org/
.. _Nox: https://nox.thea.codes/
.. _nox-poetry: https://nox-poetry.readthedocs.io/


Select an Issue
---------------

Everything is called an issue, but actually the same word is used to indicate:

- Bug reports (something does not work the way it should, it crashes with some datafiles...)
- Idea of new features (the program could do something else, a new visualization, ...)
- Code Refactoring (do the same, but with better code, maybe a better library to handle visualizations...)

Pick up one issue from the `Issue Tracker`_, or create a new one.

Use the issue comments to indicate your interest, **claim one issue for yourself**.


Code for this Issue
-------------------

Update your local copy of the repository, update your fork with the latest version:

.. code:: console

    $ git checkout main
    $ git pull upstream
    $ git push

Create a new branch, using the issue number in the name (here 372):

.. code:: console

    $ git checkout -b issue-372

All of this can be done from your IDE, just make sure you are starting a new branch from the most up-to-date
version of the repository on the MAIN branch, and you are working on this new branch.

Change all needed files, write new functions, create new files, etc...

Add a new dependency
--------------------

A new library needs to be used, for example ``altair``. It has to be added to the list of dependencies of the module:

.. code:: console

    $ poetry add altair


Time to commit
--------------

A few modifications have been made, it is time to commit them, using either command line or the IDE.

This happens within the new branch ``issue-xxx``:

.. code:: console

    $ cd track-viz
    $ git add .
    $ git commit

This will launch the pre-commit hooks. They are programs that will be launched every time there is a commit.

Each program checks something on the project's source code, and one of the programs failing is enough to refuse the
commit until the checks are satisfied:

- ``black`` will take care of formatting the source code
- ``flake8`` will check code rules (no unused variable, no unused import, ...)

Some of the checks can modify the files to make them compliant (``black``), others will require you make modifications
(``flake8``).

After modification:

.. code:: console

    $ git add .
    $ git commit

After all is OK, the commit is accepted. Push it to the repository:

.. code:: console

    $ git push --set-upstream origin issue-xxx

Create a Pull Request
---------------------

Visit the webpage of the YOUR repository fork and create a Pull Request from your new branch ``issue-xxx``. There are
instructions available on `Github Website<https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request>`_,
or on the Internet.

Mention the issue in the Pull Request, using ``#xxx`` where ``xxx`` is the issue number.

This will launch a battery of tests through github actions. The results will be either OK or Not OK.


Time to do more checks
----------------------

Unfortunately, it is likely the github action will return a negative result. You can check this on your own computer.

Unit Tests
**********

Run the existing unit tests:

.. code:: console

    $ nox -r -s tests --python=3.8

Fix any failing unit test, and do a new commit/push only when the tests are OK.

**ADD NEW TESTS** to proove bugfixing was ok, or to proove a new functionality does work.

Unit tests are located in the ``tests`` directory,
and are written using the pytest_ testing framework.

.. _pytest: https://pytest.readthedocs.io/

MyPy
****

``mypy`` takes care that all the code is properly typed:

- all functions carry type hinting for arguments and return
- all variables have type-hints that correspond to their values

It is very strict, look for help if you can't find a solution.

Commit again
************

Cycle again on modifying, commiting, pushing in the branch.

Every new commit to the branch is detected by the pull request automatically, and will launch the test battery
again.


Ready to Merge
--------------

All the checks are OK, there are new tests in place... it's ready for review. From the pull request, ask a review,
a maintainer will take care of reviewing one last time the changes, maybe ask some additions, or some code modifications,
and merge the modifications in the main branch.



.. _pull request: https://github.com/JulienMBABD/track-viz/pulls
.. github-only
.. _Code of Conduct: CODE_OF_CONDUCT.rst

Contributor Guide
=================

Thank you for your interest in improving this project.
This project is open-source under the `MIT license`_ and
welcomes contributions in the form of bug reports, feature requests, and pull requests.

Here is a list of important resources for contributors:

- `Source Code`_
- `Documentation`_
- `Issue Tracker`_
- `Code of Conduct`_

.. _MIT license: https://opensource.org/licenses/MIT
.. _Source Code: https://github.com/JulienMBABD/track-viz
.. _Documentation: https://track-viz.readthedocs.io/
.. _Issue Tracker: https://github.com/JulienMBABD/track-viz/issues

How to report a bug
-------------------

Report bugs on the `Issue Tracker`_.

When filing an issue, make sure to answer these questions:

- Which operating system and Python version are you using?
- Which version of this project are you using?
- What did you do?
- What did you expect to see?
- What did you see instead?

The best way to get your bug fixed is to provide a test case,
and/or steps to reproduce the issue.


How to request a feature
------------------------

Request features on the `Issue Tracker`_.
