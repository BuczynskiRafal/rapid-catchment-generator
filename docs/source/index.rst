Rapid Catchment Generator
=========================

Rapid Catchment Generator (RCG) appends fuzzy-logic parameterised subcatchments to
EPA SWMM models. It is available as a desktop app (``rcg-gui``), a command-line tool
(``rcg``) and the Python API documented here. See the project
`README <https://github.com/BuczynskiRafal/rapid-catchment-generator#readme>`_ for
installation, usage and the scientific background.

.. code-block:: python

   import rcg

   params = rcg.preview(5.5, "flats_and_plateaus", "Urban, moderately impervious")
   result = rcg.apply("model.inp", params)

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   api
   fuzzy
   inp_manage

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
