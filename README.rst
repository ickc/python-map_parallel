========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - |
        | |coveralls| |codecov|
        | |landscape| |scrutinizer| |codacy| |codeclimate|
    * - package
      - | |version| |wheel| |supported-versions| |supported-implementations|
        | |commits-since|
.. |docs| image:: https://readthedocs.org/projects/python-map_parallel/badge/?style=flat
    :target: https://readthedocs.org/projects/python-map_parallel
    :alt: Documentation Status

.. |coveralls| image:: https://coveralls.io/repos/ickc/python-map_parallel/badge.svg?branch=master&service=github
    :alt: Coverage Status
    :target: https://coveralls.io/r/ickc/python-map_parallel

.. |codecov| image:: https://codecov.io/gh/ickc/python-map_parallel/branch/master/graphs/badge.svg?branch=master
    :alt: Coverage Status
    :target: https://codecov.io/github/ickc/python-map_parallel

.. |landscape| image:: https://landscape.io/github/ickc/python-map_parallel/master/landscape.svg?style=flat
    :target: https://landscape.io/github/ickc/python-map_parallel/master
    :alt: Code Quality Status

.. |codacy| image:: https://img.shields.io/codacy/grade/013d60298aae4c53b33916c44a6675ab.svg
    :target: https://www.codacy.com/app/ickc/python-map_parallel
    :alt: Codacy Code Quality Status

.. |codeclimate| image:: https://codeclimate.com/github/ickc/python-map_parallel/badges/gpa.svg
   :target: https://codeclimate.com/github/ickc/python-map_parallel
   :alt: CodeClimate Quality Status

.. |version| image:: https://img.shields.io/pypi/v/map-parallel.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/project/map-parallel

.. |wheel| image:: https://img.shields.io/pypi/wheel/map-parallel.svg
    :alt: PyPI Wheel
    :target: https://pypi.org/project/map-parallel

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/map-parallel.svg
    :alt: Supported versions
    :target: https://pypi.org/project/map-parallel

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/map-parallel.svg
    :alt: Supported implementations
    :target: https://pypi.org/project/map-parallel

.. |commits-since| image:: https://img.shields.io/github/commits-since/ickc/python-map_parallel/v0.1.1.svg
    :alt: Commits since latest release
    :target: https://github.com/ickc/python-map_parallel/compare/v0.1.1...master


.. |scrutinizer| image:: https://img.shields.io/scrutinizer/quality/g/ickc/python-map_parallel/master.svg
    :alt: Scrutinizer Status
    :target: https://scrutinizer-ci.com/g/ickc/python-map_parallel/


.. end-badges

A drop-in replacement of map/starmap but in parallel with different backends.

* Free software: BSD 3-Clause License

Installation
============

::

    pip install map-parallel

You can also install the in-development version with::

    pip install https://github.com/ickc/python-map_parallel/archive/master.zip


Documentation
=============


https://python-map_parallel.readthedocs.io/


Development
===========

To run all the tests run::

    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox
