
from setuptools import setup, find_packages
import sys, os

setup(name='syschangemon',
    version='1.0',
    description="System change monitor",
    long_description="System change monitor",
    classifiers=[],
    keywords='',
    author='Erno Rigo',
    author_email='erno@rigo.info',
    url='http://www.syschangemon.info',
    license='GPLv3',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    include_package_data=True,
    zip_safe=False,
    test_suite='nose.collector',
    install_requires=[
        ### Required for testing
        'nose >= 1.3.0',
        'coverage',
        ### Required to function
        'cement >= 2.8.0',
        'globre >= 0.1.3',
        'peewee >= 2.8.0',
        'binaryornot >= 0.4.0',
        'partialhash >= 1.1.3',
        'diff_match_patch >= 20121119',
        'jinja2 == 2.6',
        'python-dateutil >= 2.5.0',
        'pytz >= 2016.1',
        'tzlocal >= 1.2.2',
        'enum34 >= 1.1.2',
        'parsedatetime >= 2.1',
        ],
    setup_requires=[],
    entry_points="""
        [console_scripts]
        syschangemon = syschangemon.cli.main:main
    """,
    namespace_packages=[],
    )
