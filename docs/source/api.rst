Public API
==========

The ``rcg`` package
-------------------

.. automodule:: rcg
   :no-members:

Functions
~~~~~~~~~

.. autofunction:: rcg.preview

.. autofunction:: rcg.apply

.. autofunction:: rcg.inspect

.. autofunction:: rcg.restore

.. autofunction:: rcg.warm_up

Value objects
~~~~~~~~~~~~~

.. autoclass:: rcg.SubcatchmentParameters
   :members: to_dict

.. autoclass:: rcg.ApplyResult
   :members: to_dict

.. autoclass:: rcg.ModelInfo
   :members:

Categories
~~~~~~~~~~

.. autoclass:: rcg.LandForm
   :members:
   :undoc-members:

.. autoclass:: rcg.LandCover
   :members:
   :undoc-members:

Exceptions
----------

.. automodule:: rcg.exceptions
   :members:
   :show-inheritance:

Command line
------------

.. automodule:: rcg.cli
   :members: main, build_parser

Model writer
------------

.. automodule:: rcg.inp_manage.writer
   :members:
