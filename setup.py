from setuptools import setup

setup(
    name='wikiautils',
    version='1.0.0',
    description='Utilities to be shared between Python projects at Wikia',
    author='Wikia Engineering',
    author_email='techteam-l@wikia-inc.com',
    install_requires=[
        'configparser'
    ],
    packages=['wikiautils']
)
