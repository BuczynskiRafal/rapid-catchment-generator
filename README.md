[![Documentation Status](https://readthedocs.org/projects/rapid-catchment-generator/badge/?version=latest)](https://rapid-catchment-generator.readthedocs.io/en/latest/?badge=latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/BuczynskiRafal/rapid-catchment-generator/blob/main/LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![GitHub Actions Build Status](https://github.com/BuczynskiRafal/rapid-catchment-generator/actions/workflows/rcg.yaml/badge.svg?branch=main)](https://github.com/BuczynskiRafal/rapid-catchment-generator/actions/workflows/rcg.yaml)
[![codecov](https://codecov.io/gh/BuczynskiRafal/rapid-catchment-generator/branch/main/graph/badge.svg?token=57X9FHJNHJ)](https://codecov.io/gh/BuczynskiRafal/rapid-catchment-generator)


# Rapid Catchment Generator

Rapid Catchment Generator (RCG) is a tool for rapid prototyping of a hydraulic model that can be read and edited with SWMM. You pick a land form, a land cover and an area; a fuzzy logic controller built from rules found in the surface runoff literature derives the slope and the imperviousness, classifies the catchment, and maps it to typical Manning coefficients and depression storage. The result is appended to your EPA SWMM `.inp` file as a complete, correctly parameterised subcatchment, which you can then refine in the SWMM GUI. RCG is available as a desktop app, a command-line tool and a Python library, and all three share the same engine and the same numbers.

* [Install](#install)
* [Desktop app](#desktop-app)
* [Command line](#command-line)
* [Python API](#python-api)
* [What gets written to the model](#what-gets-written-to-the-model)
* [Migrating from 1.x](#migrating-from-1x)
* [How it is built](#how-it-is-built) and [About](#about) (the scientific background: Tables 1-4)


## Install

RCG needs **Python 3.10 or newer**. Tkinter is no longer required.

```
pip install "rapid-catchment-generator[gui]"   # desktop app + CLI + library
pip install rapid-catchment-generator          # CLI + library only
```

From a clone of the repository:

```
python3 -m venv venv
venv/bin/pip install ".[gui]"      # or: venv/bin/pip install .
```

The `gui` extra installs PySide6. Windows, macOS and Linux are supported. Ready-made desktop builds are also
attached to each [GitHub Release](https://github.com/BuczynskiRafal/rapid-catchment-generator/releases).


## Desktop app

Launch it with either of

```
rcg-gui
python -m rcg.gui
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
   method and units) and updates as you change the inputs. The fuzzy engine is built in the background at
   start-up; the preview appears after a few seconds.
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

`rcg` (or `python -m rcg`) provides four subcommands.

```
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

Categories are case-insensitive and accept either the snake_case names or the labels printed by `rcg list-options`,
so `--land-cover "Urban, moderately impervious"` works as well. `--json` (on `add`, `preview`, `inspect` and
`list-options`) prints machine-readable output; `-v` logs debug information to stderr.

```
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
`n_imperv`, `n_perv`, `s_imperv_mm`, `s_perv_mm`, `pct_zero` and `infiltration` (a mapping with `Suction`, `Ksat`,
`IMD`, `Param4`, `Param5`), plus `to_dict()`. `rcg.apply(...)` returns an `ApplyResult` (`output_path`,
`backup_path`, `subcatchment_ids`, `raingage`, `outlet`, `flow_units`, `infiltration_method`, `written_sha256`); `rcg.inspect(path)` returns a
`ModelInfo` without loading the fuzzy engine. `rcg.restore(backup, target, expected_sha256=...)` undoes an apply and
refuses when the file was edited after RCG wrote it. `rcg.warm_up()` builds the fuzzy engine ahead of time
(a few seconds). Invalid input raises `rcg.exceptions.ValidationError` (areas must be between 0.0001 and 10 000 ha); failures while reading or writing a model raise
`ModelOperationError`, and a refused or failed restore raises `BackupError`. See the [API documentation](https://rapid-catchment-generator.readthedocs.io/).


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
  Polygons are always in metres.
* **Units:** the model's `FLOW_UNITS` decides. SI models (`CMS`, `LPS`, `MLD`) get hectares, metres and millimetres.
  US models (`CFS`, `GPM`, `MGD`) get the area in acres (x 2.4710538), the width in feet (x 3.2808399) and depression
  storage in inches (/ 25.4). Infiltration values are written as they are, without conversion.
* **Infiltration:** the row follows the `INFILTRATION` option of `[OPTIONS]`: Green-Ampt and Modified Green-Ampt get the
  Green-Ampt row (`3.5 0.5 0.25 7 0`), Horton and Modified Horton (also SWMM's default when the option is absent) get
  `3 0.5 4 7 0`, and Curve Number gets `80 0.5 7`. The defaults are in `rcg/config/defaults.json`
  (`infiltration_defaults`, keyed by method).
* **Backups:** when a model is updated in place, or when `--output` points at an existing file, the file about to be
  replaced is first copied to a `.rcg_backups` folder next to it (unless `--no-backup`).

The meaning of every written value is listed in [Table 4](#table-4-swmm-catchment-data).


## Migrating from 1.x

* `rcg.runner` is removed; use `rcg.preview` / `rcg.apply` or the `rcg` command.
* `rcg.inp_manage.inp.BuildCatchments` still works but is deprecated; it forwards to the new service.
* Python 3.10 or newer is required (1.x supported older versions).
* The Tkinter GUI is replaced by a PySide6 app (`pip install ".[gui]"`, then `rcg-gui`).
* The `RCG.exe` download from the repository is replaced by **GitHub Releases** assets, built from the PyInstaller
  specs in `packaging/`.
* Numbers are unchanged, with one intentional exception (the slope for `mountains_vegetated` on `hills_and_outcrops_of_mountain_ranges`
  is 14.33 instead of 12.16). Models in US units and with non-Green-Ampt infiltration now receive matching values; see
  [CHANGELOG.md](CHANGELOG.md).


## How it is built

The diagram below shows the construction of the Rapid Catchment Generator. The modular form of the system allows easy adaptation to specific user needs and tuning to achieve greater accuracy. 

<div align="center">
  <img src="https://github.com/BuczynskiRafal/rapid-catchment-generator/blob/main/img/rcg_schema.png">
</div>

## About
For the construction of the catchment generator, the type of landform was divided according to Table 1, 
the land cover according to Table 2. 
The categories were determined on the basis of the data presented by (Dołęga, Rogala, 1973), given below in Table 3. 


### Table 1. LandForm Categories:
| No. | LandForm Category                                |
|-----|--------------------------------------------------|
| 1   | Marshes and lowlands                             |
| 2   | Flats and plateaus                               |
| 3   | Flats and plateaus in combination with hills     |
| 4   | Hills with gentle slopes                         |
| 5   | Steeper hills and foothills                      |
| 6   | Hills and outcrops of mountain ranges            |
| 7   | Higher hills                                     |
| 8   | Mountains                                        |
| 9   | Highest mountains                                |


### Marshes and Lowlands 
**"Marshes and lowlands"** refer to areas that are typically flat or gently sloped and are often water-saturated. These regions are characterized by standing or slow-moving water, making them prone to flooding, with a high capacity for water retention. The waterlogged conditions create unique ecosystems dominated by wetland plants such as reeds, grasses, and shrubs. 

#### Characteristics: 
* **High water retention**: Marshes and lowlands have a high capacity to hold water due to their low elevation and flat topography, leading to slow drainage. 
* **Low runoff**: The saturated soil and presence of water limit the amount of runoff, as much of the precipitation remains within the area. However, excessive rainfall can lead to overflow and potential flooding. 
* **Common features**: Swamps, bogs, floodplains, and low-lying coastal areas. Vegetation in these regions is adapted to waterlogged conditions, and the soil is often rich in organic matter. 

#### When to choose this category: 
* Select this category when modeling catchments in areas that are prone to frequent water saturation, such as wetlands, floodplains, or other low-lying areas near bodies of water. This category is ideal for regions where water retention is a significant factor, and where drainage is slow due to flat terrain or a high water table. It is suitable for modeling environments that are vulnerable to flooding or are part of a natural water retention system.
***

### Flats and Plateaus 
**"Flats and plateaus"** refer to large, flat or gently elevated areas that have minimal slope. These regions are generally stable and well-suited for human habitation and agriculture, as they offer a consistent and level surface. Water flow in such areas is slow, and the overall drainage is often uniform across the terrain. 

#### Characteristics: 
* **Low slope**: These areas are either flat or have a very gentle slope, leading to slow-moving water and moderate drainage. 
* **Moderate runoff**: Due to the relatively even surface, water tends to spread out rather than quickly running off, though it can accumulate in low spots during heavy rainfall. 
* **Common features**: Plains, plateaus, agricultural fields, and urban developments on flat land. 

#### When to choose this category: 
* Select this category when modeling catchments in flat or gently elevated areas where water flow is relatively slow and spread out. This category is ideal for agricultural regions, urban developments on flat terrain, or natural plateaus with minimal slope. It's suitable for areas where runoff is moderate and drainage is even across the landscape. 
* * * 


### Flats and Plateaus in Combination with Hills
**"Flats and plateaus in combination with hills"** describes areas where flat or plateau-like terrain is interspersed with hills or gently rolling elevations. These regions feature a mix of flat surfaces and more pronounced slopes, leading to varied drainage and water flow characteristics. 

#### Characteristics:
* **Mixed topography**: A combination of flat areas and gentle hills creates diverse water flow patterns. Flat areas may retain water, while the hills encourage faster runoff. 
* **Moderate to high runoff**: Depending on the balance between flat and hilly areas, runoff can vary significantly, with water flowing more rapidly off hills and collecting in the flatter sections. 
* **Common features**: Regions with a mix of flat plains and rolling hills, such as transitional landscapes between mountain ranges and valleys. 

#### When to choose this category: 
* Use this category when modeling catchments that have a combination of flat terrain and rolling hills, creating varying water flow dynamics. It is suitable for transitional landscapes or areas where flat and hilly features are mixed, causing both retention and runoff within the same region. This category fits well for areas where water behavior is affected by both flat and sloped sections. 
* * * 

### Hills with Gentle Slopes
**"Hills with gentle slopes"** refer to areas with low-gradient hills, where the elevation changes are not steep, and the land has a more gradual slope. Water flows more freely than on flat land but at a slower pace than on steeper hills, allowing some infiltration while still generating runoff. 

#### Characteristics: 
* **Gentle slope**: The hills have a slight incline, which allows for moderate water flow without the risk of significant erosion or fast-moving runoff. 
* **Moderate runoff**: The gentle slope generates runoff, but the land’s permeability and the slow flow allow for some water absorption and moderate drainage. 
* **Common features**: Rolling hills, gently sloping highlands, and transitional areas between flatlands and mountain ranges. 

#### When to choose this category: 
* Select this category when modeling catchments in areas with gently sloping hills, where the terrain is not flat but also not steep. This category is ideal for regions where water flows more freely than in flat areas, but the risk of erosion and rapid runoff is low. It's suitable for rolling countryside or gently elevated regions with consistent but slow water movement. 

* * * 

### Steeper Hills and Foothills 
**"Steeper hills and foothills"** refer to areas where the terrain becomes more pronounced, with moderate to steep slopes leading to faster-moving water and a higher potential for runoff. These regions are often found at the base of mountain ranges or as part of hilly landscapes where elevation changes are significant. 

#### Characteristics: 
* **Steep slopes**: The steeper incline of these hills leads to faster water flow, which can result in increased runoff and potential erosion. 
* **High runoff**: Water moves quickly down these slopes, reducing the potential for infiltration and increasing the risk of erosion, particularly during heavy rainfall. 
* **Common features**: The foothills of mountain ranges, steep hillsides, and areas with rapid elevation changes. 

#### When to choose this category: 
* Choose this category when modeling catchments in areas with steep hills or foothills, where water flows rapidly and there is little opportunity for infiltration. This category is suitable for regions where runoff is significant due to steep slopes, and where erosion control and water management are necessary to handle the fast-moving water. It is ideal for foothills, mountainous areas, or regions with pronounced slopes.”


### Hills and Outcrops of Mountain Ranges
**"Hills and outcrops of mountain ranges"** refer to areas that lie at the foothills of mountains or where smaller hills and rocky outcrops are present. These areas have moderate slopes and often feature rocky or uneven terrain, but they are less steep compared to full mountain ranges. 
#### Characteristics: 
* **Moderate permeability**: The presence of rocky outcrops and soil allows for some water infiltration, but runoff can occur due to the slopes and rocky surfaces. 
* **Moderate runoff**: Water flows relatively quickly down the slopes, but the presence of vegetation and soil can help retain some moisture. Rocky outcrops may limit infiltration and increase runoff in certain areas. 
* **Common features**: Rolling hills, rocky foothills, and areas where small outcrops break through the terrain. These regions often have a mix of soil, vegetation, and exposed rock. 

#### When to choose this category: 
* Use this category when modeling catchments in areas near mountain ranges, where the terrain is characterized by a combination of hills and rocky outcrops. This category is suitable for regions with moderate slopes and mixed terrain, where water infiltration and runoff both play significant roles. 

* * * 

### Higher Hills 
**"Higher hills"** refer to more elevated hill regions with steeper slopes compared to regular hills. These areas are characterized by their higher elevation and more pronounced slopes, which influence the flow of water and runoff dynamics. 

#### Characteristics: 
* **Moderate to low permeability**: The steeper slopes mean that water tends to run off quickly, limiting infiltration. Vegetation may help retain some water, but the terrain generally promotes runoff. 
* **Higher runoff**: Water flows more quickly downhill, resulting in greater surface runoff. Steep terrain and less permeable soil contribute to this. 
* **Common features**: Large hills, highland areas, and elevated plateaus. Vegetation may still be present, but the steep slopes dominate the water flow. 

#### When to choose this category: 
* Choose this category when modeling areas with large hills that are significantly elevated and have steep slopes. These areas are often prone to quick runoff and are less likely to retain water for long periods. This category is suitable for regions where the elevation and slope greatly influence the hydrological behavior of the land. 

* * *

### Mountains
**"Mountains"** refer to areas with steep slopes and significant elevation above the surrounding terrain. These regions are characterized by dramatic changes in elevation and are often the source of rivers and streams due to their runoff potential. 

#### Characteristics: 
* **Low permeability**: The steep slopes and rocky terrain mean that water runs off quickly, with little opportunity for infiltration. Any precipitation in these areas typically flows into streams and rivers. 
* **High runoff**: Due to the steep gradients, water travels quickly downhill, leading to a significant amount of surface runoff. The lack of permeable soil in some areas also contributes to this. 
* **Common features**: High-altitude mountain ranges, steep valleys, and rugged terrain. These areas often feature sparse vegetation and exposed rock. 

#### When to choose this category: 
* Select this category when modeling catchments in mountainous regions where steep slopes and high elevation play a major role in water movement. These areas typically see high levels of runoff, which may lead to the formation of streams and rivers. This category is suitable for regions where rapid water flow and erosion are common concerns. 
* * *

### Highest Mountains 
**"Highest mountains"** refer to the most elevated and rugged areas of mountain ranges, often featuring steep cliffs, rocky terrain, and sometimes permanent snow or ice. These areas are typically at altitudes where vegetation is sparse or nonexistent, and the hydrological processes are dominated by fast runoff and extreme conditions. 

#### Characteristics: 
* **Very low permeability**: The extremely steep slopes, rocky surfaces, and potential snow cover mean that almost no water infiltrates the ground. Instead, precipitation and melting snow or ice quickly turn into runoff. 
* **Very high runoff**: Due to the steep terrain and minimal vegetation, water runs off almost immediately after precipitation or snowmelt. These areas are prone to erosion and rapid water movement. 
* **Common features**: High-altitude peaks, glaciers, and steep cliffs. The environment is often harsh, with limited plant life and challenging terrain. 

#### When to choose this category: 
* Choose this category when modeling the highest parts of mountain ranges where elevation, steep slopes, and minimal vegetation lead to extreme runoff conditions. This category is ideal for regions that are prone to rapid snowmelt, landslides, or fast-moving rivers and streams originating from the high-altitude peaks.




***

### Table 2. LandCover Categories:
| No. | LandCover Category                               |
|-----|--------------------------------------------------|
| 1   | Permeable areas                                  |
| 2   | Permeable terrain on plains                      |
| 3   | Mountains, vegetated                             |
| 4   | Mountains, rocky                                 |
| 5   | Urban, weakly impervious                         |
| 6   | Urban, moderately impervious                     |
| 7   | Urban, highly impervious                         |
| 8   | Suburban, weakly impervious                      |
| 9   | Suburban, highly impervious                      |
| 10  | Rural                                            |
| 11  | Forests                                          |
| 12  | Meadows                                          |
| 13  | Arable                                           |
| 14  | Marshes                                          |

Categories 1-9 are described in detail below; categories 10-14 get a one-line description each after the detailed ones.
In the desktop app and on the command line the land covers appear under the labels used in this table
(`rcg list-options` prints the matching snake_case names, e.g. `mountains_vegetated`).


### Permeable Areas 
**"Permeable areas"** refer to regions where the majority of the surface is highly permeable, allowing water to easily infiltrate into the ground. These areas are characterized by natural or semi-natural surfaces that absorb rainfall efficiently, reducing surface runoff and enhancing groundwater recharge.
#### Characteristics: 
* **High permeability**: The soil and surface materials are naturally absorbent, allowing most of the water to infiltrate rather than flow overland. This greatly reduces the need for stormwater management. 
* **Low runoff**: Due to the high infiltration rates, surface runoff is minimal, and flooding risks are generally lower unless the soil becomes saturated. 
* **Common features**: Natural landscapes like grasslands, forests, meadows, agricultural lands without heavy compaction, and areas with green infrastructure designed to manage stormwater naturally. 

#### When to choose this category: 
* Use this category when modeling rural or undeveloped regions where the surface consists mostly of natural vegetation, soil, or other permeable materials. This category is ideal for areas with minimal urban development, where the natural environment is the primary landscape feature and water infiltration is the dominant process.
* * * 

### Permeable Terrain on Plains 
**"Permeable terrain on plains"** refers to flat or gently sloping areas with permeable surfaces, often characterized by open landscapes that allow for good water infiltration due to the permeability of the soil or vegetation cover. These areas are typically large and open, with little obstruction to water movement. 

#### Characteristics: 
* **Moderate to high permeability**: The terrain allows water to infiltrate easily, particularly because of the flat or gently sloping nature of the plains, which prevents rapid runoff. 
* **Minimal surface runoff**: Due to the low slope and permeable surface, most rainfall infiltrates into the ground, making runoff rare unless the area becomes saturated or experiences heavy rain. 
* **Common features**: Agricultural fields, meadows, prairies, and other large expanses of flat, open land with permeable soils or vegetation. These areas often support farming, grazing, or natural ecosystems that benefit from steady water absorption. 

#### When to choose this category: 
* Choose this category when modeling flat or gently sloped areas with high water infiltration potential, particularly in rural or agricultural settings. This category is ideal for plains regions where surface water flows slowly and infiltration plays a key role in hydrological processes. It's suitable for areas with minimal development and strong natural water management.
***

### Vegetated Mountains
**"Vegetated mountains"** refers to mountainous regions covered with significant vegetation, including forests, shrubs, and other plant life. These areas typically have well-established ecosystems that can absorb water and reduce surface runoff, despite the steep terrain. 
#### Characteristics: 
* **High permeability**: The vegetation, along with the soil, allows for good water infiltration, reducing the amount of direct runoff. Root systems help anchor the soil and absorb water, stabilizing the slopes. 
* **Moderate runoff**: Although the mountainous terrain can cause water to flow quickly downhill, the presence of vegetation mitigates erosion and helps manage runoff more effectively. 
* **Common features**: Mountainous forests, wooded highlands, and natural areas with dense plant cover. These regions often have a mix of tree species, shrubs, and grasses that enhance the land’s ability to handle rainfall. 

#### When to choose this category: 
* Select this category when modeling catchments in mountainous areas with dense plant life, where vegetation plays a key role in water absorption and erosion control. This is ideal for natural, less-developed highland regions with forests or protected areas where human intervention is minimal. It’s suitable for mountain regions with significant greenery, where infiltration is higher despite the slope. 
* * * 
### Rocky Hilly Mountains 
**"Rocky hilly mountains"** refers to mountainous or hilly areas where the landscape is dominated by rocky terrain with sparse vegetation. These regions tend to have less capacity for water absorption, leading to higher surface runoff and potential erosion. #### Characteristics: 
* **Low permeability**: The rocky surfaces, combined with the limited presence of soil and vegetation, make it difficult for water to infiltrate into the ground. As a result, much of the rainfall turns into runoff. 
* **High runoff**: The lack of permeable surfaces and vegetation means that water flows quickly downhill, often leading to erosion and the rapid movement of surface water.
* **Common features**: Barren rocky mountains, cliffs, and hilly landscapes with exposed rock formations. Vegetation, if present, is often sparse, consisting of small shrubs or grasses that provide minimal infiltration capability. 

#### When to choose this category: 
* Use this category when modeling mountainous or hilly areas that have limited vegetation and are dominated by rock. These environments are typically found in arid or semi-arid regions, or at higher altitudes where plant growth is limited. It's suitable for areas where rainfall results in immediate runoff due to the rocky, impermeable nature of the terrain”
***


### Urban Weakly Impervious
**"Urban weakly impervious"** refers to areas in urban environments where the majority of the surface is permeable or semi-permeable, allowing some degree of water infiltration into the ground. In such areas, only a small portion of the land is covered by impervious materials like concrete, asphalt, or rooftops, which prevent water absorption and contribute to runoff. 
#### Characteristics: 
* **Low imperviousness (30-60%)**: These areas typically include residential zones with scattered buildings, green spaces, or areas where natural or permeable surfaces (like gardens, parks, or permeable pavements) dominate. 
* **Moderate water infiltration**: The ability of the ground to absorb water reduces the amount of surface runoff, though some impermeable surfaces still contribute to runoff, especially during intense rainfall. 
* **Common features**: Small residential areas, suburban parks, low-density developments, and areas with green infrastructure designed to manage stormwater. 
#### When to choose this category: 
* Use this category when modeling catchments for urban areas that prioritize green infrastructure, have a mix of built and natural environments, or where urban developments have relatively low coverage of impermeable surfaces. This category is suitable for residential neighborhoods with gardens, small green spaces, and fewer paved areas.”
* * * 

### Urban Moderately Impervious
**"Urban moderately impervious"** refers to areas where the proportion of impermeable surfaces is higher, but there is still a balance with permeable areas. These regions tend to have more extensive urban development compared to weakly impervious areas, but some green spaces or permeable zones still allow for limited water infiltration. 
#### Characteristics: 
* **Moderate imperviousness (50-80%)**: Impervious surfaces like roads, buildings, and parking lots cover a significant portion of the area, reducing the ability of water to infiltrate into the ground. 
* **Increased runoff**: The higher coverage of impervious surfaces results in greater surface runoff, which may require stormwater management systems to handle excess water, particularly during heavy rainfall events. 
* **Common features**: Medium-density urban developments, commercial areas with parking lots, residential neighborhoods with larger buildings, and some streets or sidewalks. 
#### When to choose this category: 
* Select this category when modeling urban areas with moderate development, where impervious surfaces make up the majority but there are still patches of permeable ground, such as lawns, small parks, or green infrastructure. It is suitable for areas like commercial districts, medium-density housing areas, or developments where runoff management is a concern, but some infiltration is still possible. 
* * * 

### Urban Highly Impervious 
**"Urban highly impervious"** refers to areas where almost all surfaces are impermeable, meaning little to no water can infiltrate into the ground. These are typically densely developed urban environments, where surfaces like concrete, asphalt, and rooftops dominate, resulting in significant amounts of runoff. 
#### Characteristics: 
* **High imperviousness (75-100%)**: Nearly all of the area is covered by buildings, roads, sidewalks, and other impermeable surfaces, leaving little room for natural water infiltration. 
* **Very high runoff**: Due to the lack of permeable surfaces, most precipitation becomes surface runoff, which can lead to challenges with stormwater management and increased risk of flooding in poorly managed systems. 
* **Common features**: Dense urban cores, industrial zones, large commercial complexes, and areas dominated by high-rise buildings, parking structures, and heavily trafficked streets. 
#### When to choose this category: 
* Choose this category when modeling highly developed urban environments where permeable surfaces are rare. This includes city centers, industrial areas, or large commercial hubs with little vegetation. In such areas, nearly all rainfall becomes runoff, necessitating robust drainage and stormwater management systems.
* * *

### Suburban Weakly Impervious 
**"Suburban weakly impervious"** refers to suburban areas where the majority of the land remains permeable, allowing significant water infiltration. These areas typically consist of low-density residential developments with open spaces, gardens, and unpaved areas. #### Characteristics: 
* **Low imperviousness (10-40%)**: A large portion of the surface area remains natural or permeable, such as lawns, gardens, and parks, with only small sections covered by impervious materials like roads or driveways. 
* **High water infiltration**: Due to the predominance of permeable surfaces, these areas experience limited surface runoff and are often effective in absorbing rainwater, reducing the strain on stormwater management systems. 
* **Common features**: Low-density suburban neighborhoods, single-family homes with large yards, and semi-rural areas with scattered development. 
#### When to choose this category: 
* Select this category when modeling suburban environments that are characterized by large open spaces and minimal impervious surfaces. It is suitable for areas with single-family homes, small streets, and large permeable surfaces where runoff is minimal and water infiltration is high. 
* * * 

### Suburban Highly Impervious 
**"Suburban highly impervious"** refers to suburban areas where impervious surfaces are more dominant, typically found in higher-density suburban developments. These areas still retain some green spaces but have more substantial coverage of paved surfaces, roads, and buildings. 
#### Characteristics: 
* **Moderate-to-high imperviousness (35-65%)**: A significant portion of the land is covered by impermeable surfaces, such as streets, driveways, and buildings, though permeable areas like lawns or small parks are still present. 
* **Increased runoff**: The presence of impervious surfaces leads to moderate surface runoff, requiring some level of stormwater management, particularly during heavy rainfall. 
* **Common features**: Higher-density suburban neighborhoods, multi-family housing developments, shopping centers, and areas with large roads and parking lots. 
#### When to choose this category: 
* Use this category when modeling suburban areas that have a higher density of development, where impervious surfaces are more prevalent but not completely dominant. It is suitable for neighborhoods with multi-family homes, small commercial areas, and suburban developments with notable impervious surfaces but still some room for water infiltration.

***



### Additional land covers (10-14)
* **Rural**: villages and farmsteads, with scattered buildings among largely permeable land.
* **Forests**: woodland with a dense canopy and litter layer; high retention and slow, rough overland flow.
* **Meadows**: grassland and pasture with continuous vegetation cover.
* **Arable**: cultivated fields; permeable soil that is often bare or compacted between crops.
* **Marshes**: wetlands and water-saturated ground with very high retention.

***

### Table 3. Runoff Coefficients According to Iszkowski

| Number | Topographic Terrain Definition                 | Drainage Coefficient ϕ |
|--------|------------------------------------------------|------------------------|
| 1      | Marshes and lowlands                           | 0.20                   |
| 2      | Flats and plateaus                             | 0.25                   |
| 3      | Flats and plateaus in combination with hills   | 0.30                   |
| 4      | Hills with gentle slopes                       | 0.35                   |
| 5      | Steeper hills and foothills                    | 0.40                   |
| 6      | Hills and outcrops of mountain ranges          | 0.45                   |
| 7      | Higher hills                                   | 0.50                   |
| 8      | Mountains                                      | 0.55                   |
| 9      | Highest mountains                              | 0.60-0.70              |


***
### Table 4. SWMM Catchment Data

| Parameter Name      | Explanation                                                                                         |
|---------------------|-----------------------------------------------------------------------------------------------------|
| Name                | Catchment names (ID) are generated as `S<n>`, the next free number.                                   |
| Raingage            | When a rain gage exists in the uploaded file, the first one will be assigned to the catchment area being built. If it does not exist, it will be added to the file along with the "timeseries" and assigned to the catchment area being generated. |
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
| Coordinate          | Square-shaped catchments are generated and placed to the right of the last polygon vertex already in the model.         |




# Bugs

If you encounter any bugs or issues while using our software, please feel free to report them on the project's [issue tracker](https://github.com/BuczynskiRafal/rapid-catchment-generator/issues). When reporting a bug, please provide as much information as possible to help us reproduce and resolve the issue, including:

* A clear and concise description of the issue
* Steps to reproduce the problem
* Expected behavior and actual behavior
* Any error messages or logs that may be relevant

Your feedback is invaluable and will help us improve the software for all users.

# Contributing

We welcome and appreciate contributions from the community! If you're interested in contributing to this project, please follow these steps:

1. Fork the repository on GitHub.
2. Create a new branch for your changes.
3. Make your changes, including updates to documentation if needed.
4. Write tests to ensure your changes are working as expected.
5. Ensure all tests pass and there are no linting or code style issues.
6. Commit your changes and create a pull request, providing a detailed description of your changes.

We will review your pull request as soon as possible and provide feedback. Once your contribution is approved, it will be merged into the main branch.

For more information about contributing to the project, please see our [contributing guide](https://github.com/BuczynskiRafal/rapid-catchment-generator/blob/main/CONTRIBUTING.md).

# License

This project is licensed under the [MIT License](https://github.com/BuczynskiRafal/rapid-catchment-generator/blob/main/LICENSE). By using, distributing, or contributing to this project, you agree to the terms and conditions of the license. Please refer to the [LICENSE.md](https://github.com/BuczynskiRafal/rapid-catchment-generator/blob/main/LICENSE) file for the full text of the license.