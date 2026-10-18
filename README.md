[![Release](https://img.shields.io/github/v/release/BuczynskiRafal/rapid-catchment-generator)](https://github.com/BuczynskiRafal/rapid-catchment-generator/releases/latest)
[![CI](https://github.com/BuczynskiRafal/rapid-catchment-generator/actions/workflows/rcg.yaml/badge.svg?branch=main)](https://github.com/BuczynskiRafal/rapid-catchment-generator/actions/workflows/rcg.yaml)
[![codecov](https://codecov.io/gh/BuczynskiRafal/rapid-catchment-generator/branch/main/graph/badge.svg)](https://codecov.io/gh/BuczynskiRafal/rapid-catchment-generator)
[![Documentation Status](https://readthedocs.org/projects/rapid-catchment-generator/badge/?version=latest)](https://rapid-catchment-generator.readthedocs.io/en/latest/?badge=latest)
[![DOI: 10.3390/w17121820](https://img.shields.io/badge/DOI-10.3390%2Fw17121820-blue.svg)](https://doi.org/10.3390/w17121820)
[![Python 3.10–3.13](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](https://github.com/BuczynskiRafal/rapid-catchment-generator/releases)
[![Typing: mypy](https://img.shields.io/badge/typing-mypy-blue.svg)](https://mypy-lang.org/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/BuczynskiRafal/rapid-catchment-generator/blob/main/LICENSE)


# Rapid Catchment Generator

Rapid Catchment Generator (RCG) is a tool for rapid prototyping of a hydraulic model that can be read and edited with EPA SWMM. You pick a land form, a land cover and an area; a fuzzy logic controller built from rules found in the surface runoff literature derives the slope and the imperviousness, classifies the catchment, and maps it to typical Manning coefficients and depression storage. The result is appended to your EPA SWMM `.inp` file as a complete, correctly parameterised subcatchment, which you can then refine in the SWMM GUI.

RCG is available as a **desktop app**, a **command-line tool** and a **Python library**, and all three share the same engine and the same numbers. The methodology and validation are published in [*Water* (2025, 17(12), 1820)](https://doi.org/10.3390/w17121820).

* [Install](#install)
* [Desktop app](#desktop-app)
* [Command line](#command-line)
* [Python API](#python-api)
* [What gets written to the model](#what-gets-written-to-the-model)
* [Migrating from 1.x](#migrating-from-1x)
* [How it is built](#how-it-is-built) and [About](#about) (the scientific background: Tables 1–4)
* [Citation](#citation)


## Install

RCG requires **Python 3.10 or newer**. Windows, macOS and Linux are supported.

```bash
# Desktop app + CLI + library (installs PySide6):
pip install "rapid-catchment-generator[gui] @ git+https://github.com/BuczynskiRafal/rapid-catchment-generator.git"

# CLI + library only:
pip install "rapid-catchment-generator @ git+https://github.com/BuczynskiRafal/rapid-catchment-generator.git"
```

From a local clone of the repository (using [`uv`](https://docs.astral.sh/uv/) or standard `venv`):

```bash
# With uv:
uv sync --extra gui
uv run rcg-gui

# Or with standard venv + pip:
python3 -m venv venv
venv/bin/pip install ".[gui]"      # or: venv/bin/pip install .
```

Ready-made standalone desktop and CLI builds are also attached to each [GitHub Release](https://github.com/BuczynskiRafal/rapid-catchment-generator/releases).


## Desktop app

Launch it with any of:

```bash
rcg-gui
python -m rcg.gui
uv run rcg-gui       # when working from a repository checkout with uv
```

<div align="center">
  <img src="https://github.com/BuczynskiRafal/rapid-catchment-generator/blob/main/img/rcg-gui.png?raw=true" alt="The RCG desktop app">
</div>

Everything happens in one window:

1. **Pick a model.** Click *Browse...* or drag and drop an `.inp` file onto the window. The card shows
   how many subcatchments the model has, its flow units and infiltration method, and which rain gage and
   outlet the new subcatchment will use.
2. **Choose the output.** *Update model in place (backup kept)* or *Save as copy...*. After a copy is
   written the app keeps working on that copy, so further additions land in the same file.
3. **Choose the terrain.** Select a land cover, a land form and an area in hectares (0.0001 to 10 000 ha
   in the library and CLI; the app's spin box starts at 0.01 ha). Hover a category to see its description.
4. **Check the live preview.** The right-hand panel shows exactly what will be written (catchment type,
   slope, imperviousness, width, Manning n, depression storage and the infiltration row in the model's
   method and units) and updates immediately as you change the inputs.
5. **Press *Add subcatchment*.**

When the model is updated in place, the original is first copied to a `.rcg_backups` folder next to it
(`<name>_backup_<timestamp>.inp`) and the new file is written atomically. Every subcatchment added in the
session appears in the history list; **Undo** on the latest entry restores its backup, and *Show in folder*
opens the folder of the written model.

| Action | Shortcut |
|---|---|
| Open a model | Ctrl+O (Cmd+O on macOS) |
| Add subcatchment | Ctrl+Return (Cmd+Return on macOS) |
| Help | F1 |


## Command line

`rcg` (or `python -m rcg`) provides four subcommands:

```bash
rcg list-options                 # land forms and land covers with their names and labels
rcg preview --area 5.5 --land-form flats_and_plateaus --land-cover urban_moderately_impervious
rcg add model.inp --area 5.5 --land-form flats_and_plateaus --land-cover urban_moderately_impervious
rcg inspect model.inp            # summarise what is in a model
```

* **`preview`** prints the computed parameters and writes nothing.
* **`add`** appends a subcatchment to `MODEL.inp`. By default the model is updated in place and a timestamped backup is
  kept in `.rcg_backups/` next to it. Use `--output OUT.inp` (`-o`) to write a copy and leave the source untouched, or
  `--no-backup` to skip the backup when updating in place.
* **`inspect`** reads a model without changing it and reports what RCG would work with: flow units (SI or US),
  infiltration method, number of existing subcatchments, and the rain gage and outlet new subcatchments would get.
* **`add --json`** additionally reports `flow_units` and `infiltration_method`. JSON floats are rounded to 4 decimals
  (the model file keeps full precision).
* **`list-options`** lists the accepted category names.

Categories are case-insensitive and accept either the `snake_case` names or the labels printed by `rcg list-options`,
so `--land-cover "Urban, moderately impervious"` works as well. `--json` (on `add`, `preview`, `inspect` and
`list-options`) prints machine-readable output; `-v` logs debug information to stderr.

```text
$ rcg preview --area 5 --land-form flats_and_plateaus --land-cover forests
Land form          Flats and plateaus
Land cover         Forests
Area               5 ha
Catchment type     forests
Slope              1.25 %
Impervious         7.00 %
Width              111.80 m
Manning n          imperv 0.4, perv 0.8
Depression storage imperv 1.27 mm, perv 7.62 mm
% zero storage     5
Infiltration       Suction=3.5, Ksat=0.5, IMD=0.25, Param4=7, Param5=0

$ rcg inspect rcg/example.inp
Model              rcg/example.inp
Flow units         CMS (SI: hectares, metres, millimetres)
Infiltration       MODIFIED_GREEN_AMPT
Subcatchments      15
Rain gage          Raingage2
Outlet             O4
Size               9,971 bytes

$ rcg inspect rcg/example.inp --json
{
  "path": "/path/to/rcg/example.inp",
  "flow_units": "CMS",
  "is_metric": true,
  "infiltration_method": "MODIFIED_GREEN_AMPT",
  "subcatchment_count": 15,
  "raingage": "Raingage2",
  "outlet": "O4",
  "size_bytes": 9971
}

$ rcg add model.inp --area 2 --land-form mountains --land-cover Forests --output copy.inp --json
```

**Exit codes:** `0` success, `2` usage or validation error (unknown category, invalid area, missing file),
`1` any other failure (for example an unreadable model). On failure the target model is never modified.
Refused with an error: read-only targets, files that are not SWMM models (EPANET networks, UTF-16/32 files, binary data),
and models with an unknown `FLOW_UNITS` or `INFILTRATION` option. If the source file changes while RCG is working
(for example it is saved in the SWMM GUI), nothing is written. Symbolic links are resolved: the real file is updated and
the link is kept.


## Python API

```python
import rcg

params = rcg.preview(5.5, "flats_and_plateaus", "Urban, moderately impervious")  # pure, no file access
print(params.slope_pct, params.impervious_pct, params.catchment_type, params.width_m)

result = rcg.apply("model.inp", params)  # backup kept, model updated in place
print(result.subcatchment_ids, result.raingage, result.outlet, result.backup_path)

copy = rcg.apply("model.inp", [params, params], output_path="copy.inp")  # several at once, one write

info = rcg.inspect("model.inp")  # ModelInfo: flow_units, is_metric, infiltration_method, ...

rcg.restore(result.backup_path, result.output_path, expected_sha256=result.written_sha256)  # undo
```

`rcg.preview(area_ha, land_form, land_cover)` returns a frozen `SubcatchmentParameters` with the fields
`land_form`, `land_cover`, `area_ha`, `slope_pct`, `impervious_pct`, `catchment_score`, `catchment_type`, `width_m`,
`n_imperv`, `n_perv`, `s_imperv_mm`, `s_perv_mm`, `pct_zero` and `infiltration` (a mapping with Green-Ampt, Horton or
Curve Number keys), plus `to_dict()`. Both `land_form` and `land_cover` accept enum members (`LandForm`, `LandCover`),
`snake_case` names, display labels, or integer category codes (`1..9` and `1..14` from Tables 1 and 2, convenient for
GIS scripts).

`rcg.apply(...)` returns an `ApplyResult` (`output_path`, `backup_path`, `subcatchment_ids`, `raingage`, `outlet`,
`flow_units`, `infiltration_method`, `written_sha256`); `rcg.inspect(path)` returns a `ModelInfo` without loading the
fuzzy engine. `rcg.restore(backup, target, expected_sha256=...)` undoes an apply and refuses when the file was edited
after RCG wrote it. `rcg.warm_up()` ensures the default fuzzy engine is initialised ahead of time. Invalid input raises
`rcg.exceptions.ValidationError` (areas must be between 0.0001 and 10 000 ha); failures while reading or writing a model
raise `ModelOperationError`, and a refused or failed restore raises `BackupError`. See the
[API documentation](https://rapid-catchment-generator.readthedocs.io/).


## What gets written to the model

RCG edits the model text directly and keeps everything it does not touch (comments, other sections, line endings) as it
was. New rows are appended to `[SUBCATCHMENTS]`, `[SUBAREAS]`, `[INFILTRATION]` and `[Polygons]`; missing sections are
created, and section headers are matched case-insensitively. The file is written to a temporary path next to the
target and moved into place, so an interrupted write cannot leave a damaged model.

* **Ids:** `S<n>`, the next free number after the existing subcatchments (`S1`, `S2`, ...), skipping names already
  used in any of the edited sections.
* **Rain gage:** the first rain gage of the model. If there is none, `RG1` is created and bound to the first time
  series, with the interval derived from that series (`1:00` if it cannot be determined); if the model has no time
  series either, the 12-value hourly design storm `generator_series` is added (interval `1:00`). An existing
  `[RAINGAGES]` table is never overwritten.
* **Outlet:** the last outfall, otherwise the last junction, otherwise the subcatchment itself.
* **Polygon:** a square of the subcatchment's area placed to the right of the last polygon vertex (or at the origin).
  Coordinates are scaled to match the model's map units (metres or feet, derived from `[MAP]` or the model flow units).
* **Units:** the model's `FLOW_UNITS` decides. SI models (`CMS`, `LPS`, `MLD`) get hectares, metres and millimetres.
  US models (`CFS`, `GPM`, `MGD`) get the area in acres ($\times 2.4710538$), the width in feet ($\times 3.2808399$) and depression
  storage in inches ($/ 25.4$). Infiltration values are written as they are, without conversion.
* **Infiltration:** the row follows the `INFILTRATION` option of `[OPTIONS]`: Green-Ampt and Modified Green-Ampt get the
  Green-Ampt row (`3.5 0.5 0.25 7 0`), Horton and Modified Horton (also SWMM's default when the option is absent) get
  `3 0.5 4 7 0`, and Curve Number gets `80 0.5 7` (custom per-subcatchment infiltration values in `SubcatchmentParameters.infiltration`
  are written when their keys match the model's method). The defaults live in `rcg/config/defaults.json`
  (`infiltration_defaults`, keyed by method).
* **Backups:** when a model is updated in place, or when `--output` points at an existing file, the file about to be
  replaced is first copied to a `.rcg_backups` folder next to it (unless `--no-backup`), keeping up to 10 recent
  backups per model.

The meaning of every written value is listed in [Table 4](#table-4-swmm-catchment-data).


## Migrating from 1.x

* `rcg.runner` is removed; use `rcg.preview` / `rcg.apply` or the `rcg` command.
* `rcg.inp_manage.inp.BuildCatchments` still works but is deprecated; it forwards to the new service.
* Python 3.10 or newer is required (1.x supported older versions).
* The Tkinter GUI is replaced by a PySide6 app (`pip install ".[gui]"`, then `rcg-gui`).
* The `RCG.exe` download from the repository is replaced by **GitHub Releases** assets, built from the PyInstaller
  specs in `packaging/`.
* Numbers are unchanged, with two intentional rule fixes: the slope for `mountains_vegetated` on
  `hills_and_outcrops_of_mountain_ranges` is `14.33` instead of `12.16`, and `urban_highly_impervious` on
  `flats_and_plateaus` classifies as `urban` (score `75.0`) instead of `mountains`. Models in US units and with
  non-Green-Ampt infiltration now receive matching values.


## How it is built

All three interfaces (`rcg.gui`, `rcg.cli`, and the `rcg` Python API) call into a single service and validation layer (`rcg.service` and `rcg.validation`), which coordinates the Mamdani fuzzy inference engine (`rcg.fuzzy`) and the atomic `.inp` writer and backup manager (`rcg.inp_manage`).

<div align="center">
  <img src="https://github.com/BuczynskiRafal/rapid-catchment-generator/blob/main/img/rcg_schema.png?raw=true" alt="Architecture of Rapid Catchment Generator">
</div>


## About

For the construction of the catchment generator, the type of landform is divided according to **Table 1** and the land cover according to **Table 2**. The topographic categories were determined on the basis of the data presented by Dołęga and Rogala (1973), given in **Table 3**, and formalised in the fuzzy-logic framework described by [Dawidowicz and Buczyński (2025)](https://doi.org/10.3390/w17121820).


### Table 1. LandForm Categories

| No. | LandForm Category                            | Summary                                                                                              |
|-----|----------------------------------------------|------------------------------------------------------------------------------------------------------|
| 1   | Marshes and lowlands                         | Flat, often water-saturated ground with slow drainage and high retention (wetlands, floodplains).    |
| 2   | Flats and plateaus                           | Large flat or gently elevated terrain with minimal slope and slow, even drainage.                    |
| 3   | Flats and plateaus in combination with hills | Flat terrain interspersed with gentle hills; water is retained on flats and runs off faster on hills.|
| 4   | Hills with gentle slopes                     | Low-gradient rolling hills with moderate overland flow and partial infiltration.                     |
| 5   | Steeper hills and foothills                  | Moderate to steep slopes at mountain bases with rapid flow and high runoff.                          |
| 6   | Hills and outcrops of mountain ranges        | Foothills with rocky outcrops and uneven terrain where both infiltration and runoff matter.          |
| 7   | Higher hills                                 | Elevated hills with pronounced slopes, quick runoff, and limited infiltration.                       |
| 8   | Mountains                                    | Steep, high-relief terrain with rocky ground, sparse vegetation, and high runoff.                    |
| 9   | Highest mountains                            | Rugged high-altitude terrain (cliffs, bare rock, snow/ice) with very high, immediate runoff.         |

<details>
<summary><strong>Detailed descriptions of LandForm categories (click to expand)</strong></summary>

#### 1. Marshes and Lowlands
**"Marshes and lowlands"** refer to areas that are typically flat or gently sloped and are often water-saturated. These regions are characterized by standing or slow-moving water, making them prone to flooding, with a high capacity for water retention. The waterlogged conditions create unique ecosystems dominated by wetland plants such as reeds, grasses, and shrubs.

* **High water retention**: Marshes and lowlands have a high capacity to hold water due to their low elevation and flat topography, leading to slow drainage.
* **Low runoff**: The saturated soil and presence of water limit the amount of runoff, as much of the precipitation remains within the area. However, excessive rainfall can lead to overflow and potential flooding.
* **Common features**: Swamps, bogs, floodplains, and low-lying coastal areas. Vegetation in these regions is adapted to waterlogged conditions, and the soil is often rich in organic matter.
* **When to choose this category**: Select this category when modeling catchments in areas that are prone to frequent water saturation, such as wetlands, floodplains, or other low-lying areas near bodies of water. This category is ideal for regions where water retention is a significant factor, and where drainage is slow due to flat terrain or a high water table. It is suitable for modeling environments that are vulnerable to flooding or are part of a natural water retention system.

---

#### 2. Flats and Plateaus
**"Flats and plateaus"** refer to large, flat or gently elevated areas that have minimal slope. These regions are generally stable and well-suited for human habitation and agriculture, as they offer a consistent and level surface. Water flow in such areas is slow, and the overall drainage is often uniform across the terrain.

* **Low slope**: These areas are either flat or have a very gentle slope, leading to slow-moving water and moderate drainage.
* **Moderate runoff**: Due to the relatively even surface, water tends to spread out rather than quickly running off, though it can accumulate in low spots during heavy rainfall.
* **Common features**: Plains, plateaus, agricultural fields, and urban developments on flat land.
* **When to choose this category**: Select this category when modeling catchments in flat or gently elevated areas where water flow is relatively slow and spread out. This category is ideal for agricultural regions, urban developments on flat terrain, or natural plateaus with minimal slope. It is suitable for areas where runoff is moderate and drainage is even across the landscape.

---

#### 3. Flats and Plateaus in Combination with Hills
**"Flats and plateaus in combination with hills"** describes areas where flat or plateau-like terrain is interspersed with hills or gently rolling elevations. These regions feature a mix of flat surfaces and more pronounced slopes, leading to varied drainage and water flow characteristics.

* **Mixed topography**: A combination of flat areas and gentle hills creates diverse water flow patterns. Flat areas may retain water, while the hills encourage faster runoff.
* **Moderate to high runoff**: Depending on the balance between flat and hilly areas, runoff can vary significantly, with water flowing more rapidly off hills and collecting in the flatter sections.
* **Common features**: Regions with a mix of flat plains and rolling hills, such as transitional landscapes between mountain ranges and valleys.
* **When to choose this category**: Use this category when modeling catchments that have a combination of flat terrain and rolling hills, creating varying water flow dynamics. It is suitable for transitional landscapes or areas where flat and hilly features are mixed, causing both retention and runoff within the same region.

---

#### 4. Hills with Gentle Slopes
**"Hills with gentle slopes"** refer to areas with low-gradient hills, where the elevation changes are not steep, and the land has a more gradual slope. Water flows more freely than on flat land but at a slower pace than on steeper hills, allowing some infiltration while still generating runoff.

* **Gentle slope**: The hills have a slight incline, which allows for moderate water flow without the risk of significant erosion or fast-moving runoff.
* **Moderate runoff**: The gentle slope generates runoff, but the land's permeability and the slow flow allow for some water absorption and moderate drainage.
* **Common features**: Rolling hills, gently sloping highlands, and transitional areas between flatlands and mountain ranges.
* **When to choose this category**: Select this category when modeling catchments in areas with gently sloping hills, where the terrain is not flat but also not steep. This category is ideal for regions where water flows more freely than in flat areas, but the risk of erosion and rapid runoff is low.

---

#### 5. Steeper Hills and Foothills
**"Steeper hills and foothills"** refer to areas where the terrain becomes more pronounced, with moderate to steep slopes leading to faster-moving water and a higher potential for runoff. These regions are often found at the base of mountain ranges or as part of hilly landscapes where elevation changes are significant.

* **Steep slopes**: The steeper incline of these hills leads to faster water flow, which can result in increased runoff and potential erosion.
* **High runoff**: Water moves quickly down these slopes, reducing the potential for infiltration and increasing the risk of erosion, particularly during heavy rainfall.
* **Common features**: The foothills of mountain ranges, steep hillsides, and areas with rapid elevation changes.
* **When to choose this category**: Choose this category when modeling catchments in areas with steep hills or foothills, where water flows rapidly and there is little opportunity for infiltration. This category is suitable for regions where runoff is significant due to steep slopes, and where erosion control and water management are necessary to handle the fast-moving water.

---

#### 6. Hills and Outcrops of Mountain Ranges
**"Hills and outcrops of mountain ranges"** refer to areas that lie at the foothills of mountains or where smaller hills and rocky outcrops are present. These areas have moderate slopes and often feature rocky or uneven terrain, but they are less steep compared to full mountain ranges.

* **Moderate permeability**: The presence of rocky outcrops and soil allows for some water infiltration, but runoff can occur due to the slopes and rocky surfaces.
* **Moderate runoff**: Water flows relatively quickly down the slopes, but the presence of vegetation and soil can help retain some moisture. Rocky outcrops may limit infiltration and increase runoff in certain areas.
* **Common features**: Rolling hills, rocky foothills, and areas where small outcrops break through the terrain. These regions often have a mix of soil, vegetation, and exposed rock.
* **When to choose this category**: Use this category when modeling catchments in areas near mountain ranges, where the terrain is characterized by a combination of hills and rocky outcrops. This category is suitable for regions with moderate slopes and mixed terrain, where water infiltration and runoff both play significant roles.

---

#### 7. Higher Hills
**"Higher hills"** refer to more elevated hill regions with steeper slopes compared to regular hills. These areas are characterized by their higher elevation and more pronounced slopes, which influence the flow of water and runoff dynamics.

* **Moderate to low permeability**: The steeper slopes mean that water tends to run off quickly, limiting infiltration. Vegetation may help retain some water, but the terrain generally promotes runoff.
* **Higher runoff**: Water flows more quickly downhill, resulting in greater surface runoff. Steep terrain and less permeable soil contribute to this.
* **Common features**: Large hills, highland areas, and elevated plateaus. Vegetation may still be present, but the steep slopes dominate the water flow.
* **When to choose this category**: Choose this category when modeling areas with large hills that are significantly elevated and have steep slopes. These areas are often prone to quick runoff and are less likely to retain water for long periods.

---

#### 8. Mountains
**"Mountains"** refer to areas with steep slopes and significant elevation above the surrounding terrain. These regions are characterized by dramatic changes in elevation and are often the source of rivers and streams due to their runoff potential.

* **Low permeability**: The steep slopes and rocky terrain mean that water runs off quickly, with little opportunity for infiltration. Any precipitation in these areas typically flows into streams and rivers.
* **High runoff**: Due to the steep gradients, water travels quickly downhill, leading to a significant amount of surface runoff. The lack of permeable soil in some areas also contributes to this.
* **Common features**: High-altitude mountain ranges, steep valleys, and rugged terrain. These areas often feature sparse vegetation and exposed rock.
* **When to choose this category**: Select this category when modeling catchments in mountainous regions where steep slopes and high elevation play a major role in water movement.

---

#### 9. Highest Mountains
**"Highest mountains"** refer to the most elevated and rugged areas of mountain ranges, often featuring steep cliffs, rocky terrain, and sometimes permanent snow or ice. These areas are typically at altitudes where vegetation is sparse or nonexistent, and the hydrological processes are dominated by fast runoff and extreme conditions.

* **Very low permeability**: The extremely steep slopes, rocky surfaces, and potential snow cover mean that almost no water infiltrates the ground. Instead, precipitation and melting snow or ice quickly turn into runoff.
* **Very high runoff**: Due to the steep terrain and minimal vegetation, water runs off almost immediately after precipitation or snowmelt. These areas are prone to erosion and rapid water movement.
* **Common features**: High-altitude peaks, glaciers, and steep cliffs. The environment is often harsh, with limited plant life and challenging terrain.
* **When to choose this category**: Choose this category when modeling the highest parts of mountain ranges where elevation, steep slopes, and minimal vegetation lead to extreme runoff conditions.

</details>


### Table 2. LandCover Categories

In the desktop app and on the command line the land covers appear under the labels used in this table (`rcg list-options` prints the matching `snake_case` names, e.g. `mountains_vegetated`).

| No. | LandCover Category           | Summary                                                                                              |
|-----|------------------------------|------------------------------------------------------------------------------------------------------|
| 1   | Permeable areas              | Natural or semi-natural highly permeable surfaces (grassland, forest, green infrastructure).         |
| 2   | Permeable terrain on plains  | Open, flat or gently sloping permeable land such as fields, meadows, and prairies.                   |
| 3   | Mountains, vegetated         | Mountain slopes with dense vegetation whose roots and soil absorb water and limit erosion.           |
| 4   | Mountains, rocky             | Rocky hills and mountains with sparse vegetation and rapid surface runoff.                           |
| 5   | Urban, weakly impervious     | Urban areas with ~30–60% impervious cover (scattered buildings, gardens, parks).                     |
| 6   | Urban, moderately impervious | Medium-density urban areas with ~50–80% impervious cover (commercial zones, residential blocks).     |
| 7   | Urban, highly impervious     | Dense city cores and industrial zones with ~75–100% impervious cover.                                |
| 8   | Suburban, weakly impervious  | Low-density suburbs with ~10–40% impervious cover (single-family homes with large yards).            |
| 9   | Suburban, highly impervious  | Denser suburbs with ~35–65% impervious cover (multi-family housing, shopping centers, wide roads).   |
| 10  | Rural                        | Villages and farmsteads with scattered buildings among largely permeable land.                       |
| 11  | Forests                      | Woodland with a dense canopy and litter layer; high retention and slow, rough overland flow.         |
| 12  | Meadows                      | Grassland and pasture with continuous vegetation cover.                                              |
| 13  | Arable                       | Cultivated fields; permeable soil that is often bare or compacted between crops.                     |
| 14  | Marshes                      | Wetlands and water-saturated ground with very high retention.                                        |

<details>
<summary><strong>Detailed descriptions of LandCover categories (click to expand)</strong></summary>

#### 1. Permeable Areas
**"Permeable areas"** refer to regions where the majority of the surface is highly permeable, allowing water to easily infiltrate into the ground. These areas are characterized by natural or semi-natural surfaces that absorb rainfall efficiently, reducing surface runoff and enhancing groundwater recharge.

* **High permeability**: The soil and surface materials are naturally absorbent, allowing most of the water to infiltrate rather than flow overland. This greatly reduces the need for stormwater management.
* **Low runoff**: Due to the high infiltration rates, surface runoff is minimal, and flooding risks are generally lower unless the soil becomes saturated.
* **Common features**: Natural landscapes like grasslands, forests, meadows, agricultural lands without heavy compaction, and areas with green infrastructure designed to manage stormwater naturally.
* **When to choose this category**: Use this category when modeling rural or undeveloped regions where the surface consists mostly of natural vegetation, soil, or other permeable materials.

---

#### 2. Permeable Terrain on Plains
**"Permeable terrain on plains"** refers to flat or gently sloping areas with permeable surfaces, often characterized by open landscapes that allow for good water infiltration due to the permeability of the soil or vegetation cover. These areas are typically large and open, with little obstruction to water movement.

* **Moderate to high permeability**: The terrain allows water to infiltrate easily, particularly because of the flat or gently sloping nature of the plains, which prevents rapid runoff.
* **Minimal surface runoff**: Due to the low slope and permeable surface, most rainfall infiltrates into the ground, making runoff rare unless the area becomes saturated or experiences heavy rain.
* **Common features**: Agricultural fields, meadows, prairies, and other large expanses of flat, open land with permeable soils or vegetation.
* **When to choose this category**: Choose this category when modeling flat or gently sloped areas with high water infiltration potential, particularly in rural or agricultural settings.

---

#### 3. Mountains, Vegetated
**"Mountains, vegetated"** refers to mountainous regions covered with significant vegetation, including forests, shrubs, and other plant life. These areas typically have well-established ecosystems that can absorb water and reduce surface runoff, despite the steep terrain.

* **High permeability**: The vegetation, along with the soil, allows for good water infiltration, reducing the amount of direct runoff. Root systems help anchor the soil and absorb water, stabilizing the slopes.
* **Moderate runoff**: Although the mountainous terrain can cause water to flow quickly downhill, the presence of vegetation mitigates erosion and helps manage runoff more effectively.
* **Common features**: Mountainous forests, wooded highlands, and natural areas with dense plant cover.
* **When to choose this category**: Select this category when modeling catchments in mountainous areas with dense plant life, where vegetation plays a key role in water absorption and erosion control.

---

#### 4. Mountains, Rocky
**"Mountains, rocky"** refers to mountainous or hilly areas where the landscape is dominated by rocky terrain with sparse vegetation. These regions tend to have less capacity for water absorption, leading to higher surface runoff and potential erosion.

* **Low permeability**: The rocky surfaces, combined with the limited presence of soil and vegetation, make it difficult for water to infiltrate into the ground. As a result, much of the rainfall turns into runoff.
* **High runoff**: The lack of permeable surfaces and vegetation means that water flows quickly downhill, often leading to erosion and the rapid movement of surface water.
* **Common features**: Barren rocky mountains, cliffs, and hilly landscapes with exposed rock formations.
* **When to choose this category**: Use this category when modeling mountainous or hilly areas that have limited vegetation and are dominated by rock.

---

#### 5. Urban, Weakly Impervious
**"Urban, weakly impervious"** refers to areas in urban environments where the majority of the surface is permeable or semi-permeable, allowing some degree of water infiltration into the ground. In such areas, only a small portion of the land is covered by impervious materials like concrete, asphalt, or rooftops.

* **Low imperviousness (30–60%)**: These areas typically include residential zones with scattered buildings, green spaces, or areas where natural or permeable surfaces (like gardens, parks, or permeable pavements) dominate.
* **Moderate water infiltration**: The ability of the ground to absorb water reduces the amount of surface runoff, though some impermeable surfaces still contribute to runoff, especially during intense rainfall.
* **Common features**: Small residential areas, suburban parks, low-density developments, and areas with green infrastructure designed to manage stormwater.
* **When to choose this category**: Use this category when modeling catchments for urban areas that prioritize green infrastructure, have a mix of built and natural environments, or where urban developments have relatively low coverage of impermeable surfaces.

---

#### 6. Urban, Moderately Impervious
**"Urban, moderately impervious"** refers to areas where the proportion of impermeable surfaces is higher, but there is still a balance with permeable areas. These regions tend to have more extensive urban development compared to weakly impervious areas, but some green spaces or permeable zones still allow for limited water infiltration.

* **Moderate imperviousness (50–80%)**: Impervious surfaces like roads, buildings, and parking lots cover a significant portion of the area, reducing the ability of water to infiltrate into the ground.
* **Increased runoff**: The higher coverage of impervious surfaces results in greater surface runoff, which may require stormwater management systems to handle excess water, particularly during heavy rainfall events.
* **Common features**: Medium-density urban developments, commercial areas with parking lots, residential neighborhoods with larger buildings, and some streets or sidewalks.
* **When to choose this category**: Select this category when modeling urban areas with moderate development, where impervious surfaces make up the majority but there are still patches of permeable ground, such as lawns, small parks, or green infrastructure.

---

#### 7. Urban, Highly Impervious
**"Urban, highly impervious"** refers to areas where almost all surfaces are impermeable, meaning little to no water can infiltrate into the ground. These are typically densely developed urban environments, where surfaces like concrete, asphalt, and rooftops dominate, resulting in significant amounts of runoff.

* **High imperviousness (75–100%)**: Nearly all of the area is covered by buildings, roads, sidewalks, and other impermeable surfaces, leaving little room for natural water infiltration.
* **Very high runoff**: Due to the lack of permeable surfaces, most precipitation becomes surface runoff, which can lead to challenges with stormwater management and increased risk of flooding in poorly managed systems.
* **Common features**: Dense urban cores, industrial zones, large commercial complexes, and areas dominated by high-rise buildings, parking structures, and heavily trafficked streets.
* **When to choose this category**: Choose this category when modeling highly developed urban environments where permeable surfaces are rare, such as city centers, industrial areas, or large commercial hubs.

---

#### 8. Suburban, Weakly Impervious
**"Suburban, weakly impervious"** refers to suburban areas where the majority of the land remains permeable, allowing significant water infiltration. These areas typically consist of low-density residential developments with open spaces, gardens, and unpaved areas.

* **Low imperviousness (10–40%)**: A large portion of the surface area remains natural or permeable, such as lawns, gardens, and parks, with only small sections covered by impervious materials like roads or driveways.
* **High water infiltration**: Due to the predominance of permeable surfaces, these areas experience limited surface runoff and are often effective in absorbing rainwater, reducing the strain on stormwater management systems.
* **Common features**: Low-density suburban neighborhoods, single-family homes with large yards, and semi-rural areas with scattered development.
* **When to choose this category**: Select this category when modeling suburban environments that are characterized by large open spaces and minimal impervious surfaces.

---

#### 9. Suburban, Highly Impervious
**"Suburban, highly impervious"** refers to suburban areas where impervious surfaces are more dominant, typically found in higher-density suburban developments. These areas still retain some green spaces but have more substantial coverage of paved surfaces, roads, and buildings.

* **Moderate-to-high imperviousness (35–65%)**: A significant portion of the land is covered by impermeable surfaces, such as streets, driveways, and buildings, though permeable areas like lawns or small parks are still present.
* **Increased runoff**: The presence of impervious surfaces leads to moderate surface runoff, requiring some level of stormwater management, particularly during heavy rainfall.
* **Common features**: Higher-density suburban neighborhoods, multi-family housing developments, shopping centers, and areas with large roads and parking lots.
* **When to choose this category**: Use this category when modeling suburban areas that have a higher density of development, where impervious surfaces are more prevalent but not completely dominant.

---

#### 10–14. Additional Land Covers
* **10. Rural**: villages and farmsteads, with scattered buildings among largely permeable land.
* **11. Forests**: woodland with a dense canopy and litter layer; high retention and slow, rough overland flow.
* **12. Meadows**: grassland and pasture with continuous vegetation cover.
* **13. Arable**: cultivated fields; permeable soil that is often bare or compacted between crops.
* **14. Marshes**: wetlands and water-saturated ground with very high retention.

</details>


### Table 3. Runoff Coefficients According to Iszkowski

| Number | Topographic Terrain Definition                 | Drainage Coefficient $\phi$ |
|--------|------------------------------------------------|-----------------------------|
| 1      | Marshes and lowlands                           | 0.20                        |
| 2      | Flats and plateaus                             | 0.25                        |
| 3      | Flats and plateaus in combination with hills   | 0.30                        |
| 4      | Hills with gentle slopes                       | 0.35                        |
| 5      | Steeper hills and foothills                    | 0.40                        |
| 6      | Hills and outcrops of mountain ranges          | 0.45                        |
| 7      | Higher hills                                   | 0.50                        |
| 8      | Mountains                                      | 0.55                        |
| 9      | Highest mountains                              | 0.60–0.70                   |


### Table 4. SWMM Catchment Data

| Parameter Name      | Explanation                                                                                         |
|---------------------|-----------------------------------------------------------------------------------------------------|
| Name                | Catchment names (ID) are generated as `S<n>`, the next free number.                                   |
| Raingage            | When a rain gage exists in the uploaded file, the first one will be assigned to the catchment area being built. If it does not exist, it will be added to the file along with the `timeseries` and assigned to the catchment area being generated. |
| Outlet              | The last outfall of the model; if there is none, the last junction; if there is none, the name of the generated catchment area itself. |
| Area                | A parameter passed by the user.                                                                     |
| Percent Imperv      | Parameter calculated as described above and assigned to the catchment area.                          |
| Width               | Characteristic width `sqrt(area_m2) / 2`, i.e. half the side of the square catchment (area in square metres), rounded to 2 decimals. |
| Percent Slope       | Parameter calculated as described above and assigned to the catchment area.                          |
| N-Imperv            | The value taken based on the linguistic variables passed to the fuzzy logic controller, which were previously mapped with Manning coefficients. |
| N-Perv              | The value taken based on the linguistic variables passed to the fuzzy logic controller, which were previously mapped with Manning coefficients. |
| Dstore-Imperv       | The value taken based on the linguistic variables passed to the fuzzy logic controller, which were previously mapped with typical storage values. |
| Dstore-Perv         | The value taken based on the linguistic variables passed to the fuzzy logic controller, which were previously mapped with typical storage values. |
| Percent Zero Imperv | The value taken based on the linguistic variables passed to the fuzzy logic controller, which were previously mapped with typical storage values. |
| RouteTo             | Runoff from the impervious and pervious areas flows directly to the outlet (`OUTLET`).              |
| Coordinate          | Square-shaped catchments are generated and placed to the right of the last polygon vertex already in the model (scaled to the model's map units). |


## Citation

If you use Rapid Catchment Generator (RCG) in your research or engineering projects, please cite the following paper:

> Dawidowicz, J.; Buczyński, R. Rapid SWMM Catchment Prototyping Using Fuzzy Logic: Analyzing Catchment Features for Enhanced Efficiency. *Water* **2025**, *17*(12), 1820. https://doi.org/10.3390/w17121820

```bibtex
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
```


## Contributing

Bug reports and feature requests can be opened on the [issue tracker](https://github.com/BuczynskiRafal/rapid-catchment-generator/issues). Development setup, testing commands, and pull request conventions are documented in [CONTRIBUTING.md](https://github.com/BuczynskiRafal/rapid-catchment-generator/blob/main/CONTRIBUTING.md). Security vulnerabilities should be reported privately as described in [SECURITY.md](https://github.com/BuczynskiRafal/rapid-catchment-generator/blob/main/SECURITY.md).


## License

Released under the [MIT License](https://github.com/BuczynskiRafal/rapid-catchment-generator/blob/main/LICENSE).