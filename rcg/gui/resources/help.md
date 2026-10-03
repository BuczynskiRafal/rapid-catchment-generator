# Rapid Catchment Generator

Rapid Catchment Generator (RCG) appends a correctly parameterised subcatchment to an
EPA SWMM model. You describe the terrain with two categories and an area; a fuzzy-logic
controller derives the slope and imperviousness, classifies the catchment and maps it
to typical Manning coefficients and depression storage values. Refine the result in the
SWMM GUI afterwards if you have better local data.

## Adding a subcatchment

1. **SWMM model**: choose an `.inp` file with *Browse...* or drop it anywhere on the window.
   The line under the file shows its subcatchment count, flow units, infiltration method and size.
2. **Output**: update the model in place (a timestamped backup is kept), or save the result as a
   copy. After the copy is written, RCG keeps working on the copy: further subcatchments are added
   to it, in place.
3. **Land cover**: what covers the ground (urban, suburban, forests, meadows...).
4. **Land form**: the shape of the terrain, from marshes and lowlands to the highest mountains.
5. **Area** in hectares (0.01 to 10 000 ha).
6. Press **Add subcatchment**. The subcatchment is built from the inputs as they were when you
   pressed it, even if you change them while it is being written.

The **Preview** shows exactly what will be written, and updates as you change the inputs.
The first preview appears once the fuzzy engine is ready, which takes a few seconds after start-up.
The infiltration row follows the model's infiltration method (Green-Ampt is shown until a model
is chosen). For models in US units (CFS, GPM, MGD) the area, width and depression storage are
converted to acres, feet and inches when they are written.

## Backups and undo

When the model is updated in place, the original file is first copied to a `.rcg_backups`
folder next to the model (`<name>_backup_<timestamp>.inp`). The file is then written
atomically, so an interrupted write never leaves a damaged model behind.

The **History** list shows everything added in this session. *Undo* on the latest entry
copies its backup back over the model; the backup file itself is kept. *Show in folder*
opens the folder that contains the written model.

## Keyboard shortcuts

| Action | Shortcut |
|---|---|
| Open a model | Ctrl+O (Cmd+O on macOS) |
| Add subcatchment | Ctrl+Return (Cmd+Return on macOS) |
| Help | F1 |
| Move between fields | Tab / Shift+Tab |

## Land form categories

Land forms are ordered from the flattest to the steepest terrain; the order matters to the fuzzy rules.

| No. | Land form | Description |
|---|---|---|
| 1 | Marshes and lowlands | Flat, often water-saturated ground with slow drainage and high water retention: swamps, bogs, floodplains, low-lying coastal areas. |
| 2 | Flats and plateaus | Large flat or gently elevated areas with minimal slope. Water spreads out rather than running off; drainage is slow and even. Plains, plateaus, fields, urban development on flat land. |
| 3 | Flats and plateaus in combination with hills | Flat terrain interspersed with gentle hills: water is retained on the flats and runs off faster on the slopes. Typical of transitional landscapes. |
| 4 | Hills with gentle slopes | Low-gradient rolling hills. Water flows more freely than on flat land but slowly enough for some infiltration. |
| 5 | Steeper hills and foothills | Moderate to steep slopes, often at the base of mountain ranges. Fast flow, high runoff and erosion risk. |
| 6 | Hills and outcrops of mountain ranges | Foothills with rocky outcrops and uneven terrain; moderate slopes where both infiltration and runoff matter. |
| 7 | Higher hills | Elevated hills with pronounced slopes. Water runs off quickly and infiltration is limited. |
| 8 | Mountains | Steep, high terrain with rocky ground and sparse vegetation. Little infiltration, high runoff. |
| 9 | Highest mountains | The most rugged high-altitude terrain (cliffs, snow, ice). Almost all precipitation and meltwater runs off. |

## Land cover categories

| No. | Land cover | Description |
|---|---|---|
| 1 | Permeable areas | Mostly natural, highly permeable surfaces (grassland, forest, uncompacted farmland, green infrastructure). Most rainfall infiltrates. |
| 2 | Permeable terrain on plains | Open, flat or gently sloping permeable land such as fields, meadows and prairies. Runoff is rare unless the soil is saturated. |
| 3 | Mountains, vegetated | Mountain slopes with dense vegetation. Roots and soil absorb water and limit erosion despite the slope. |
| 4 | Mountains, rocky | Rocky hills and mountains with sparse vegetation. Rainfall turns into runoff almost immediately. |
| 5 | Urban, weakly impervious | Urban areas with roughly 30-60 % impervious cover: scattered buildings, gardens, parks. |
| 6 | Urban, moderately impervious | Medium-density urban areas with roughly 50-80 % impervious cover: commercial districts, parking, larger residential blocks. |
| 7 | Urban, highly impervious | Dense city cores, industrial zones and large commercial complexes with roughly 75-100 % impervious cover. |
| 8 | Suburban, weakly impervious | Low-density suburbs with roughly 10-40 % impervious cover: single-family homes with large yards. |
| 9 | Suburban, highly impervious | Denser suburbs with roughly 35-65 % impervious cover: multi-family housing, shopping centres, wide roads. |
| 10 | Rural | Villages and farmsteads: scattered buildings among largely permeable land. |
| 11 | Forests | Woodland with a dense canopy and litter layer: high retention and slow, rough overland flow. |
| 12 | Meadows | Grassland and pasture with continuous vegetation cover. |
| 13 | Arable | Cultivated fields: permeable soil that is often bare or compacted between crops. |
| 14 | Marshes | Wetlands and water-saturated ground with very high retention. |

## What is written to the model

| SWMM field | Source |
|---|---|
| Name | `S<n>`, the next free number in the model. |
| Rain gage | The first rain gage in the model. If there is none, `RG1` is created and bound to the first time series (a design storm series is added when the model has none). |
| Outlet | The last outfall, otherwise the last junction, otherwise the subcatchment itself. |
| Area | The area you entered. |
| % Imperv, % Slope | Results of the fuzzy-logic controller. |
| Width | Characteristic width `sqrt(area) / 2` of a square subcatchment. |
| N-Imperv, N-Perv | Manning coefficients mapped from the catchment type. |
| Dstore-Imperv, Dstore-Perv | Typical depression storage mapped from the catchment type. |
| % Zero-Imperv | Share of the impervious area without depression storage, mapped from the catchment type. |
| Infiltration | Green-Ampt defaults. |
| Polygon | A square of the given area placed to the right of the existing drawing. |

## Background

The land form categories follow the topographic classification behind Iszkowski's runoff
coefficients (after Dołęga and Rogala, 1973):

| No. | Topographic terrain | Runoff coefficient |
|---|---|---|
| 1 | Marshes and lowlands | 0.20 |
| 2 | Flats and plateaus | 0.25 |
| 3 | Flats and plateaus in combination with hills | 0.30 |
| 4 | Hills with gentle slopes | 0.35 |
| 5 | Steeper hills and foothills | 0.40 |
| 6 | Hills and outcrops of mountain ranges | 0.45 |
| 7 | Higher hills | 0.50 |
| 8 | Mountains | 0.55 |
| 9 | Highest mountains | 0.60-0.70 |

Found a problem? Please report it on the
[issue tracker](https://github.com/BuczynskiRafal/rapid-catchment-generator/issues).
