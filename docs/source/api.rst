Public API Reference
====================

Top-Level Package (``rcg``)
---------------------------

.. automodule:: rcg
   :no-members:

Service Functions
~~~~~~~~~~~~~~~~~

.. autofunction:: rcg.preview

.. autofunction:: rcg.apply

.. autofunction:: rcg.inspect

.. autofunction:: rcg.restore

.. autofunction:: rcg.warm_up

Value Objects
~~~~~~~~~~~~~

.. autoclass:: rcg.SubcatchmentParameters
   :members: to_dict

.. autoclass:: rcg.ApplyResult
   :members: to_dict

.. autoclass:: rcg.ModelInfo
   :members: to_dict

Category Enumerations
~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: rcg.LandForm
   :members:
   :undoc-members:

.. autoclass:: rcg.LandCover
   :members:
   :undoc-members:

Catchment Helpers & SWMM Constants (``rcg.catchment``)
------------------------------------------------------

.. automodule:: rcg.catchment
   :members: width_m, is_metric, infiltration_for, base_infiltration_method, label, lookup_land_form, lookup_land_cover, FLOW_UNITS_SI, FLOW_UNITS_US, INFILTRATION_METHODS, INFILTRATION_FIELDS, KNOWN_INFILTRATION_KEYS, LAND_FORM_LABELS, LAND_COVER_LABELS

Input Validation (``rcg.validation``)
-------------------------------------

.. automodule:: rcg.validation
   :members: validate_area, validate_land_form, validate_land_cover, validate_inp_path, validate_parameters, min_area_ha, max_area_ha

Configuration & Logging
-----------------------

Default Parameters (``rcg.config``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: rcg.config.loader
   :members: Defaults, load_defaults, INFILTRATION_DEFAULT_METHODS

Logging Helpers (``rcg.logging_config``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: rcg.logging_config
   :members: get_logger, setup_logging, set_log_level, log_file_path

Exceptions (``rcg.exceptions``)
-------------------------------

.. automodule:: rcg.exceptions
   :members:
   :show-inheritance:

Command-Line Interface (``rcg.cli``)
------------------------------------

.. automodule:: rcg.cli
   :members: main, build_parser, JSON_DECIMALS
