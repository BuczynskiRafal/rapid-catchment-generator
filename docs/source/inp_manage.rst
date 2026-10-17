SWMM File Management (``rcg.inp_manage``)
=========================================

.. automodule:: rcg.inp_manage
   :no-members:

Model Writer (``rcg.inp_manage.writer``)
----------------------------------------

.. automodule:: rcg.inp_manage.writer
   :members: append_subcatchments, inspect_model, DESIGN_STORM
   :show-inheritance:

Model Backups (``rcg.inp_manage.backups``)
------------------------------------------

.. automodule:: rcg.inp_manage.backups
   :members:
   :show-inheritance:

Legacy 1.x Facade (``rcg.inp_manage.inp``)
------------------------------------------

.. deprecated:: 2.0
   Use :func:`rcg.preview` and :func:`rcg.apply` instead. This module is a thin
   compatibility facade and will be removed in a future release.

.. automodule:: rcg.inp_manage.inp
   :members: BuildCatchments, ModelParameters
   :show-inheritance:
