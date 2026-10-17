Rapid Catchment Generator
=========================

**Rapid Catchment Generator (RCG)** appends fuzzy-logic parameterised subcatchments to
EPA SWMM ``.inp`` models. Given a **land form**, a **land cover**, and an **area** in
hectares, a Mamdani fuzzy inference engine derives terrain slope and imperviousness,
classifies the catchment into one of seven hydrological types, and maps it to typical
Manning roughness coefficients, depression storage, and infiltration parameters.

RCG provides three interfaces backed by the same deterministic engine:

* **Python API** (:mod:`rcg`) — programmatic inspection, parameter preview, atomic model writes, and backup restoration.
* **Command-Line Interface** (``rcg``) — scriptable subcommands with human-readable and ``--json`` output.
* **Desktop Application** (``rcg-gui``) — single-window PySide6 interface with live parameter preview and one-click undo.

The methodology and hydrological validation are published in
`Water 2025, 17(12), 1820 <https://doi.org/10.3390/w17121820>`_.

Installation
------------

RCG requires **Python 3.10 or newer** (Linux, macOS, and Windows).

.. code-block:: bash

   # CLI + Python library:
   pip install rapid-catchment-generator

   # Desktop GUI + CLI + Python library (adds PySide6):
   pip install "rapid-catchment-generator[gui]"

From a local clone using `uv <https://docs.astral.sh/uv/>`_:

.. code-block:: bash

   uv sync --extra gui
   uv run rcg --help
   uv run rcg-gui

Quickstart
----------

Python API
~~~~~~~~~~

.. code-block:: python

   import rcg

   # 1. Inspect an existing SWMM model (fast, read-only, no fuzzy engine loaded)
   info = rcg.inspect("model.inp")
   print(info.flow_units, info.infiltration_method, info.subcatchment_count)

   # 2. Preview computed parameters (accepts enums, snake_case names, labels, or GIS integer codes)
   params = rcg.preview(5.5, "flats_and_plateaus", "Urban, moderately impervious")
   print(params.catchment_type, params.slope_pct, params.impervious_pct, params.width_m)

   # 3. Append one or more subcatchments atomically (creates a backup in .rcg_backups/)
   result = rcg.apply("model.inp", params)
   print(result.subcatchment_ids, result.raingage, result.outlet, result.backup_path)

   # 4. Undo the write if needed (refuses if the model was modified externally since)
   rcg.restore(result.backup_path, result.output_path, expected_sha256=result.written_sha256)

Command Line
~~~~~~~~~~~~

.. code-block:: bash

   # List all 9 land forms and 14 land covers:
   rcg list-options

   # Preview computed SWMM parameters without modifying any file:
   rcg preview --area 5.5 --land-form flats_and_plateaus --land-cover urban_moderately_impervious

   # Inspect a SWMM model's units, infiltration method, rain gage, and outlet:
   rcg inspect model.inp

   # Append a subcatchment in place (automatic backup kept in .rcg_backups/):
   rcg add model.inp --area 5.5 --land-form flats_and_plateaus --land-cover urban_moderately_impervious

   # Write to a separate copy and emit machine-readable JSON:
   rcg add model.inp --area 2.0 --land-form mountains --land-cover Forests --output copy.inp --json

Desktop Application
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   rcg-gui
   # or: python -m rcg.gui

Citation
--------

If you use Rapid Catchment Generator in research or engineering projects, please cite:

   Dawidowicz, J.; Buczyński, R. Rapid SWMM Catchment Prototyping Using Fuzzy Logic:
   Analyzing Catchment Features for Enhanced Efficiency. *Water* **2025**, *17* (12), 1820.
   https://doi.org/10.3390/w17121820

.. code-block:: bibtex

   @article{DawidowiczBuczynski2025RCG,
     author         = {Dawidowicz, Jacek and Buczy{\'n}ski, Rafa{\l}},
     title          = {Rapid {SWMM} Catchment Prototyping Using Fuzzy Logic: Analyzing Catchment Features for Enhanced Efficiency},
     journal        = {Water},
     volume         = {17},
     number         = {12},
     article-number = {1820},
     year           = {2025},
     publisher      = {MDPI},
     issn           = {2073-4441},
     doi            = {10.3390/w17121820},
     url            = {https://www.mdpi.com/2073-4441/17/12/1820}
   }

.. toctree::
   :maxdepth: 2
   :caption: Documentation

   guide
   api
   fuzzy
   inp_manage

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
