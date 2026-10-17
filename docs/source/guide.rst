User & Engineering Guide
========================

This guide describes the input categories, the fuzzy inference parameterization,
the SWMM ``.inp`` writer contract, and the command-line interface.

Input Categories
----------------

:func:`rcg.preview` accepts category inputs in four interchangeable formats (the CLI
accepts the two string formats — ``snake_case`` identifiers and human-readable labels):

1. **Enum members** (:class:`rcg.LandForm` / :class:`rcg.LandCover` — Python API)
2. **Integer codes** (``1–9`` for land form, ``1–14`` for land cover — Python API, convenient for GIS attribute tables and rasters)
3. **Snake-case identifiers** (e.g. ``"flats_and_plateaus"``, ``"urban_moderately_impervious"``)
4. **Human-readable labels** (case-insensitive, e.g. ``"Flats and plateaus"``, ``"Urban, moderately impervious"``)

Land Form Categories (1–9)
~~~~~~~~~~~~~~~~~~~~~~~~~~

Each land form corresponds to a topographic terrain class and is associated with a
triangular slope membership function :math:`(a, b, c)` in percent:

.. list-table::
   :header-rows: 1
   :widths: 6 32 28 16 18

   * - Code
     - Identifier (``snake_case``)
     - Label
     - Slope ``(a, b, c)`` [%]
     - Summary
   * - ``1``
     - ``marshes_and_lowlands``
     - Marshes and lowlands
     - ``(0, 0, 1)``
     - Flat, water-saturated wetlands and floodplains with high retention.
   * - ``2``
     - ``flats_and_plateaus``
     - Flats and plateaus
     - ``(0, 1, 2.5)``
     - Flat or gently elevated plains and plateaus with minimal slope.
   * - ``3``
     - ``flats_and_plateaus_in_combination_with_hills``
     - Flats and plateaus in combination with hills
     - ``(1, 2.5, 5)``
     - Flat terrain interspersed with gentle rolling hills.
   * - ``4``
     - ``hills_with_gentle_slopes``
     - Hills with gentle slopes
     - ``(2.5, 5, 8)``
     - Low-gradient rolling hills with moderate overland flow.
   * - ``5``
     - ``steeper_hills_and_foothills``
     - Steeper hills and foothills
     - ``(5, 8, 15)``
     - Moderate-to-steep slopes at mountain bases with rapid runoff.
   * - ``6``
     - ``hills_and_outcrops_of_mountain_ranges``
     - Hills and outcrops of mountain ranges
     - ``(8, 15, 20)``
     - Foothills with rocky outcrops and uneven terrain.
   * - ``7``
     - ``higher_hills``
     - Higher hills
     - ``(15, 20, 30)``
     - Elevated hills with pronounced slopes and limited infiltration.
   * - ``8``
     - ``mountains``
     - Mountains
     - ``(20, 30, 40)``
     - Steep, high-relief terrain with rocky ground and sparse vegetation.
   * - ``9``
     - ``highest_mountains``
     - Highest mountains
     - ``(30, 50, 60)``
     - Rugged alpine terrain (cliffs, bare rock) with immediate runoff.

Land Cover Categories (1–14)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each land cover describes surface permeability and maps to an imperviousness triangular
membership function :math:`(a, b, c)` in percent:

.. list-table::
   :header-rows: 1
   :widths: 6 28 26 18 22

   * - Code
     - Identifier (``snake_case``)
     - Label
     - Impervious ``(a, b, c)`` [%]
     - Summary
   * - ``1``
     - ``permeable_areas``
     - Permeable areas
     - *(rule-dependent)*
     - Natural or semi-natural highly permeable surfaces.
   * - ``2``
     - ``permeable_terrain_on_plains``
     - Permeable terrain on plains
     - *(rule-dependent)*
     - Open, flat or gently sloping permeable fields and prairies.
   * - ``3``
     - ``mountains_vegetated``
     - Mountains, vegetated
     - ``(5, 15, 25)``
     - Mountain slopes with dense vegetation and root stabilization.
   * - ``4``
     - ``mountains_rocky``
     - Mountains, rocky
     - ``(20, 40, 60)``
     - Rocky hills and mountains with sparse vegetation.
   * - ``5``
     - ``urban_weakly_impervious``
     - Urban, weakly impervious
     - ``(30, 45, 60)``
     - Low-density urban zones with gardens, parks, and scattered buildings.
   * - ``6``
     - ``urban_moderately_impervious``
     - Urban, moderately impervious
     - ``(50, 65, 80)``
     - Medium-density urban residential and commercial blocks.
   * - ``7``
     - ``urban_highly_impervious``
     - Urban, highly impervious
     - ``(75, 85, 100)``
     - Dense city cores and industrial zones.
   * - ``8``
     - ``suburban_weakly_impervious``
     - Suburban, weakly impervious
     - ``(10, 25, 40)``
     - Single-family suburban housing with large yards.
   * - ``9``
     - ``suburban_highly_impervious``
     - Suburban, highly impervious
     - ``(35, 50, 65)``
     - Denser suburbs, multi-family housing, and commercial centers.
   * - ``10``
     - ``rural``
     - Rural
     - ``(7, 11, 15)``
     - Villages and farmsteads among largely permeable land.
   * - ``11``
     - ``forests``
     - Forests
     - ``(5, 7, 9)``
     - Woodland with dense canopy and litter layer.
   * - ``12``
     - ``meadows``
     - Meadows
     - ``(2, 5, 8)``
     - Grassland and pasture with continuous vegetation cover.
   * - ``13``
     - ``arable``
     - Arable
     - ``(0, 2, 4)``
     - Cultivated agricultural fields.
   * - ``14``
     - ``marshes``
     - Marshes
     - ``(0, 0, 2)``
     - Wetlands and water-saturated ground.

Fuzzy Inference & Subcatchment Parameters
-----------------------------------------

Inference Architecture
~~~~~~~~~~~~~~~~~~~~~~

The fuzzy inference system (:class:`rcg.fuzzy.engine.FuzzyEngine`) evaluates a complete
:math:`9 \times 14 = 126` rule matrix (:data:`rcg.fuzzy.rule_definitions.RULE_TABLE`)
using Mamdani implication and centroid defuzzification over integer output grids:

* **Slope** (``slope_pct``): universe :math:`[0, 60]\%`, attainable centroid interval :math:`[0.333\%, 46.667\%]`.
* **Imperviousness** (``impervious_pct``): universe :math:`[0, 100]\%`, attainable centroid interval :math:`[0.667\%, 86.667\%]`.
* **Catchment Score** (``catchment_score``): universe :math:`[0, 100]`, attainable centroid interval :math:`[5.0, 87.333]`.

For the standard 126 category pairs, :class:`~rcg.fuzzy.engine.FuzzyEngine` serves
precomputed exact results in :math:`O(1)` time without importing or running ``skfuzzy``
at call time. When custom :class:`~rcg.fuzzy.memberships.Memberships` or a custom
:class:`~rcg.fuzzy.rule_engine.RuleEngine` are injected, the engine lazily compiles and
executes the full ``skfuzzy`` control systems.

Characteristic Width
~~~~~~~~~~~~~~~~~~~~

The characteristic overland flow width (:func:`rcg.catchment.width_m`) is modelled as half
the side of an equivalent square subcatchment of area :math:`A_{\text{ha}}` (in hectares):

.. math::

   W_{\text{m}} = \operatorname{round}\!\left(\frac{\sqrt{A_{\text{ha}} \cdot 10\,000}}{2},\; 2\right)

Output Catchment Classes & Subarea Parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The defuzzified ``catchment_score`` is classified into the output term with the highest
membership degree, which selects the Manning roughness coefficients and depression
storage depths from ``rcg/config/defaults.json``:

.. list-table::
   :header-rows: 1
   :widths: 18 20 14 14 18 18 12

   * - Catchment Type
     - Score ``(a, b, c)``
     - ``n_imperv``
     - ``n_perv``
     - ``s_imperv`` (mm / in)
     - ``s_perv`` (mm / in)
     - ``pct_zero`` [%]
   * - ``urban``
     - ``(0, 0, 15)``
     - ``0.013``
     - ``0.15``
     - ``1.27`` / ``0.05``
     - ``5.08`` / ``0.20``
     - ``50``
   * - ``suburban``
     - ``(0, 15, 30)``
     - ``0.013``
     - ``0.24``
     - ``1.27`` / ``0.05``
     - ``5.08`` / ``0.20``
     - ``40``
   * - ``rural``
     - ``(15, 30, 45)``
     - ``0.013``
     - ``0.41``
     - ``1.27`` / ``0.05``
     - ``5.08`` / ``0.20``
     - ``35``
   * - ``forests``
     - ``(30, 45, 60)``
     - ``0.40``
     - ``0.80``
     - ``1.27`` / ``0.05``
     - ``7.62`` / ``0.30``
     - ``5``
   * - ``meadows``
     - ``(45, 60, 75)``
     - ``0.15``
     - ``0.41``
     - ``1.27`` / ``0.05``
     - ``5.08`` / ``0.20``
     - ``10``
   * - ``arable``
     - ``(60, 75, 90)``
     - ``0.06``
     - ``0.17``
     - ``1.27`` / ``0.05``
     - ``5.08`` / ``0.20``
     - ``10``
   * - ``mountains``
     - ``(75, 87, 100)``
     - ``0.013``
     - ``0.05``
     - ``1.27`` / ``0.05``
     - ``5.08`` / ``0.20``
     - ``10``

Infiltration Parameters
~~~~~~~~~~~~~~~~~~~~~~~

When writing to a model, RCG inspects ``[OPTIONS] INFILTRATION`` (default ``HORTON`` when
absent) and writes the matching ``[INFILTRATION]`` row (:func:`rcg.catchment.infiltration_for`):

.. list-table::
   :header-rows: 1
   :widths: 30 40 30

   * - SWMM ``INFILTRATION`` Option
     - Parameters (in order)
     - Default Row Written
   * - ``GREEN_AMPT``, ``MODIFIED_GREEN_AMPT``
     - ``Suction``, ``Ksat``, ``IMD`` (plus trailing ``Param4``, ``Param5``)
     - ``3.5  0.5  0.25  7  0``
   * - ``HORTON``, ``MODIFIED_HORTON``
     - ``MaxRate``, ``MinRate``, ``Decay``, ``DryTime``, ``MaxInfil``
     - ``3  0.5  4  7  0``
   * - ``CURVE_NUMBER``
     - ``CurveNum`` (or ``CurvNo``), ``Conductivity``, ``DryTime``
     - ``80  0.5  7``

To override infiltration parameters for a specific subcatchment in Python, use
:func:`dataclasses.replace` with keys matching the target model's infiltration method:

.. code-block:: python

   from dataclasses import replace
   import rcg

   base = rcg.preview(4.0, "hills_with_gentle_slopes", "arable")
   custom = replace(base, infiltration={"CurveNum": 74, "Conductivity": 0.5, "DryTime": 5})
   rcg.apply("cn_model.inp", custom)

SWMM ``.inp`` Writer & Safety Guarantees
----------------------------------------

:func:`rcg.apply` (backed by :func:`rcg.inp_manage.writer.append_subcatchments`) is
designed so that an interrupted or invalid operation can never corrupt the user's model:

1. **Symlink-preserving path resolution**: Source and destination paths are resolved with
   :func:`os.path.realpath`, so a symlinked model is updated at its real target and
   backups are placed next to the real file.
2. **Structural check**: Rejects empty files, binary files (NUL bytes), UTF-16/UTF-32
   files, and EPANET network files before any modification occurs.
3. **Lossless text editing**: Section headers are matched case-insensitively. Rows are
   appended to ``[SUBCATCHMENTS]``, ``[SUBAREAS]``, ``[INFILTRATION]``, and
   ``[Polygons]`` (creating missing sections if needed). Every untouched byte—comments,
   custom sections, line endings (``LF`` or ``CRLF``), UTF-8 BOM, and 8-bit encodings—is
   preserved byte-for-byte.
4. **Automatic unit conversion**:

   * **SI models** (``FLOW_UNITS`` in ``CMS``, ``LPS``, ``MLD``): area in hectares, width
     in metres, depression storage in millimetres.
   * **US customary models** (``FLOW_UNITS`` in ``CFS``, ``GPM``, ``MGD``): area in acres
     (:math:`\times 2.4710538`), width in feet (:math:`\times 3.2808399`), depression
     storage in inches (:math:`/ 25.4`).

5. **Polygon coordinate scaling**: A square polygon is placed starting from the last
   existing polygon vertex in ``[Polygons]`` (or at the origin ``(0, 0)`` when none
   exists), scaled in metres or feet according to ``[MAP] UNITS`` (``METERS`` or
   ``FEET``, falling back to ``FLOW_UNITS`` when ``[MAP] UNITS`` is ``DEGREES``,
   ``NONE``, or absent).
6. **Rain gage and outlet selection**:

   * Uses the first existing rain gage in ``[RAINGAGES]``. If none exists, creates
     ``RG1`` bound to the first ``[TIMESERIES]`` (or appends the 12-hour design storm
     ``generator_series`` with ``1:00`` interval).
   * Routes runoff to the last outfall in ``[OUTFALLS]``, else the last junction in
     ``[JUNCTIONS]``, else to the subcatchment itself.

7. **Double verification**: Before touching the disk, RCG verifies that every generated
   ``S<n>`` identifier appears the expected number of times across all edited sections
   and that ``swmmio`` can parse every new subcatchment back from the rendered text.
8. **Backups & atomic replacement**:

   * When overwriting an existing file (unless ``backup=False``), RCG copies it to
     ``<dir>/.rcg_backups/<stem>_backup_<timestamp>.inp`` and prunes older backups
     (retaining up to 10 recent backups per model within 30 days, always keeping at
     least the newest backup).
   * Re-reads the source file to guard against concurrent external edits, writes to a
     sibling temporary file with ``os.fsync``, and replaces the destination via
     :func:`os.replace`.
   * :func:`rcg.restore` atomically restores a backup and optionally verifies
     ``expected_sha256`` (:attr:`rcg.ApplyResult.written_sha256`) so external edits made
     after RCG wrote the file are never overwritten.

Command-Line Interface Reference
--------------------------------

The ``rcg`` command (also invocable as ``python -m rcg``) provides four subcommands:

.. list-table::
   :header-rows: 1
   :widths: 22 48 30

   * - Subcommand
     - Arguments & Flags
     - Description
   * - ``rcg add``
     - ``MODEL.inp --area HA --land-form NAME --land-cover NAME [-o OUT.inp] [--no-backup] [--json]``
     - Compute parameters and append a subcatchment to ``MODEL.inp`` (or ``OUT.inp``).
   * - ``rcg preview``
     - ``--area HA --land-form NAME --land-cover NAME [--json]``
     - Compute and print subcatchment parameters without touching any file.
   * - ``rcg inspect``
     - ``MODEL.inp [--json]``
     - Report flow units, infiltration method, subcatchment count, rain gage, and outlet.
   * - ``rcg list-options``
     - ``[--json]``
     - List all 9 land forms and 14 land covers (``snake_case`` names and labels).

Global options:

* ``--version`` — print package version and exit.
* ``-v``, ``--verbose`` — log ``DEBUG`` records to ``stderr``.

Exit codes:

* ``0`` — success.
* ``2`` — CLI usage error or :class:`~rcg.exceptions.ValidationError` (invalid area, unknown category, missing ``.inp`` file).
* ``1`` — runtime or model error (:class:`~rcg.exceptions.RCGError`, unreadable/non-SWMM file, read-only target).
