python-commons
==============

Common Python libraries to share between projects at Wikia

Working with these packages
---------------------------

Don't run the ``setup.py`` directly. Use the ``build.py`` convenience script::

    $ python build.py --help

    This is a convenience script for building, installing, and uploading
    individual packages from the wikia.common namespace. This should be run
    from inside a virtual environment.

    Usage: build.py (install|develop|upload) <package>

    Commands:

        install     Install the package into your virtual environment.
        develop     Install the package using pip's "editable" mode.
        upload      Build a source distribution and upload it to Wikia's
                    private PyPI server (requires a working ~/.pypirc file).

    Arguments:

        <package>   The name of a package directory in wikia/common/

Development
-----------

python-commons comes with a ``Makefile`` that provides shortcuts for frequently performed commands:

* ``make test`` runs unit tests for all packages
* ``make coverage`` generates test coverage report for all packages
* ``make lint`` runs pep8 and pylint tools

Troubleshooting
---------------

If developing on a local machine make sure you have the latest version of pip:

    pip install -U pip
    
Uploading packages
------------------

We use Artifactory as package repository. Please log in there generate credentials - https://wikia-inc.atlassian.net/wiki/display/GEN/Artifactory+-+Internal+package+repositories

In your ``~/.pypirc`` add the following::

   [distutils]
   index-servers =
       pypi
       wikia
   
   ...
   
   [wikia]
   repository = https://artifactory.wikia-inc.com/artifactory/api/pypi/pypi/
   username = <your username>
   password = <generated API key>

When ready to upload the updated package simply run ``python build.py upload`` from root directory of this repository. Your package should be visible on https://artifactory.wikia-inc.com/artifactory/pypi/
