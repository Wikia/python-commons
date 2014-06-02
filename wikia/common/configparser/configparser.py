"""
configparser.py
===============

This module extends the configparser backport from Python 3.2+:
<https://pypi.python.org/pypi/configparser>

It adds duck typing by assuming all config values are JSON strings. It
also provides a helper function for getting a list of config files from
standard locations. See the docstrings in the methods below for more
detailed information.

## Basic Usage

    >>> from wikiautils.configparser import ConfigParser
    >>> config = ConfigParser()
    >>> config.read(config.get_paths('foo'))
    ['/etc/foo/foo.conf']
    >>> config['foo']['bar']
    u'baz'

"""

from __future__ import absolute_import
import glob
import json
import os
import re

import configparser


class ExtendedInterpolation(configparser.ExtendedInterpolation):
    """Subclass of `configparser.ExtendedInterpolation`"""

    def before_get(self, parser, section, option, value, defaults):
        # There's a problem in `configparser.ExtendedInterpolation` for
        # options that reference other options without specifying the
        # section. The custom `get()` function in `ConfigParser` further
        # down in this file is not used. The solution is to add the
        # section when it's not present.
        value = re.sub(r'\$\{([^}\:]+)\}', r'${' + section + r':\1}', value)
        return super(ExtendedInterpolation, self).before_get(
            parser, section, option, value, defaults)


class ConfigParser(configparser.ConfigParser):
    """Subclass of `configparser.ConfigParser`"""

    def __init__(self, *args, **kwargs):
        kwargs.update(dict(
            interpolation=ExtendedInterpolation(),
            delimiters=('='), comment_prefixes=('#'), inline_comment_prefixes=('#')
        ))
        super(ConfigParser, self).__init__(*args, **kwargs)

    @staticmethod
    def get_paths(app, names=None):
        """Generates a list of standard paths of config files

        For example, for `app='foo'`, the following files are looked for
        in this order:

        - /etc/foo/foo.conf
        - /etc/foo/conf.d/*.conf
        - the environment variable FOO_CONFIG
        - ~/.foo.conf

        The optional `names` argument can be list of additional names to
        look for in `/etc/{app}/`. For example, for
        `app='foo', names=['foo', 'bar', 'baz']`, the following files
        are looked for in this order:

        - /etc/foo/foo.conf
        - /etc/foo/bar.conf
        - /etc/foo/baz.conf
        - /etc/foo/conf.d/*.conf
        - the environment variable FOO_CONFIG
        - ~/.foo.conf

        This method **only** returns the list of files. If you want to
        actually load them, use `read()`.
        """
        pattern = r'^[A-Za-z][A-Za-z0-9_\-]{2,}$'
        if not re.match(pattern, app):
            raise Exception('Program name for get_paths() must match the pattern ' + pattern)

        if names is None:
            names = [app]

        # Main files from /etc/{app}/
        filenames = ['/etc/{app}/{name}.conf'.format(app=app, name=name) for name in names]

        # Files from /etc/{app}/conf.d/
        filenames += glob.glob('/etc/{app}/conf.d/*.conf'.format(app=app))

        # Path defined by {APP}_CONFIG environment variable
        env_name = app.replace('-', '_').upper() + '_CONFIG'
        if env_name in os.environ:
            filenames.append(os.environ[env_name])

        # User file ~/.{app}.conf
        filenames.append(os.path.expanduser('~/.{app}.conf'.format(app=app)))

        return [filename for filename in filenames if os.path.isfile(filename)]

    @staticmethod
    def _encode(value):
        """Encodes a value to JSON"""
        return json.dumps(value)

    @staticmethod
    def _decode(section, option, value, raw=False):
        """Decodes a value from a config file before getting it

        The value can basically be any valid JSON string. Some examples:
        - string: "foo"
        - int: 123
        - float: 123.456
        - list: ["foo", "bar"]
        - dict: {"foo": "bar"}
        """
        if raw:
            if len(value) > 1 and value[0] == '"' and value[-1] == '"':
                # We at least need to strip quotes
                return value[1:-1]
            else:
                return value
        try:
            return json.loads(value)
        except (TypeError, ValueError):
            raise Exception('Invalid value for "' + section + ':' + option + '"')

    def get(self, section, option, raw=False, **kwargs):
        value = super(ConfigParser, self).get(section, option, raw=raw, **kwargs)
        value = self._decode(section, option, value, raw=raw)
        return value

    def items(self, section=None, raw=False, **kwargs):
        if section is None:
            return super(ConfigParser, self).items(raw=raw, **kwargs)
        raw_items = super(ConfigParser, self).items(section, raw=raw, **kwargs)
        transformed_items = []
        for (option, value) in raw_items:
            transformed_items.append((option, self._decode(section, option, value, raw=raw)))
        return transformed_items

    def set(self, section, option, value=None):
        value = self._encode(value)
        return super(ConfigParser, self).set(section, option, value)

    def write(self, *args, **kwargs):
        del args, kwargs
        raise AttributeError("'ConfigParser' object has no attribute 'write'")

    def read_docstring(self, obj):
        r"""Reads config values from the second part of an object's
        docstring split once by `\n---\n`"""
        parts = obj.__doc__.split('\n---\n', 1)
        if len(parts) < 2 or not parts[1]:
            return
        return self.read_string(unicode(parts[1]))
