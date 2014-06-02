python-commons
==============

Common Python libraries to share between projects at Wikia

Working with these packages
---------------------------

Don't run the ``setup.py`` directly. Use the ``build.py`` convenience script::

    $ python build.py --help

    This ia a convenience script for building, installing, and uploading
    individual packages from the wikia.common namespace. This should be run
    from inside a virtual environment.

    USAGE: build.py (install|develop|upload) <package>

