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
