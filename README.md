[![Documentation Status](https://readthedocs.org/projects/rapid-catchment-generator/badge/?version=latest)](https://rapid-catchment-generator.readthedocs.io/en/latest/?badge=latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/BuczynskiRafal/catchments_simulation/blob/main/LICENSE)
[![PyPI version fury.io](https://badge.fury.io/py/ansicolortags.svg)](https://pypi.org/project/rcg/)
[![GitHub Actions Build Status](https://github.com/BuczynskiRafal/rapid-catchment-generator/actions/workflows/rcg.yaml/badge.svg?branch=main)](https://github.com/BuczynskiRafal/rapid-catchment-generator/actions/workflows/rcg.yaml/badge.svg?branch=main)
[![codecov](https://codecov.io/gh/BuczynskiRafal/rapid-catchment-generator/branch/main/graph/badge.svg?token=57X9FHJNHJ)](https://codecov.io/gh/BuczynskiRafal/rapid-catchment-generator)


# Rapid catchment generator
Tool for rapid prototyping of a hydraulic model that can be read and edited with SWMM. The generator was created using feature analysis and surface runoff research from the literature. Fuzzy logic controller rules were developed using parameterized categories of soil, slope, and permeability. The catchment configuration procedure was simplified by mapping typical storage and Manning's coefficients. The use of fuzzy logic rules allows the system to be modified to adjust the categories to certain situations. The use of membership functions allows us to increase computation accuracy and customize the tool to diverse applications. Following alteration of the catchment in the SWMM GUI allows for accurate portrayal of the real condition of the catchment.


## Using the Graphical User Interface (GUI)
One of the most user-friendly ways to utilize the capabilities of RCG is through its intuitive graphical user interface (GUI) application. The GUI provides an easy-to-navigate environment where users can input parameters, manipulate data, and visualize results, all without the need for complex coding or scripting.

## Getting Started
To get started with the RCG GUI, simply follow these steps:
1. Click the file "RCG.exe", gitchub will take you to "https://github.com/BuczynskiRafal/rapid-catchment-generator/blob/main/RCG.exe". On the right side of the window is the "download" button, download the file. 
2. Double-click on the file downloaded to the desired location. After installation, the RCG window will appear. 
3. Fill in the data and generate the catchment with the "Run" button.

<div align="center">
  <img src="https://github.com/BuczynskiRafal/rapid-catchment-generator/blob/main/img/RCG_GUI.png">
</div>

## Requirements
* Python 3

## Usage from terminal
Create a virtual environment:
```
python3 -m venv venv
```
Download and install the required dependencies: 

```
python3 pip install -r requirements
``` 
To run the script, use the following command:
```
python3 rcg.runner file path
``` 
where `file path` is the path to the SWMM model file.

Enter data into the terminal according to the instructions it displays.
The file is automatically saved in the same directory.  

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
| 3   | Vegetated mountains                              |
| 4   | Rocky hilly mountains                            |
| 5   | Urban weakly impervious                          |
| 6   | Urban moderately impervious                      |
| 7   | Urban highly impervious                          |
| 8   | Suburban weakly impervious                       |
| 9   | Suburban highly impervious                       |


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
| Name                | Catchment names (ID) are generated by adding a number.                                               |
| Raingage            | When "raingage" exists in the uploaded file, it will be assigned to the catchment area being built. If it does not exist, it will be added to the file along with the "timeseries" and assigned to the catchment area being generated. |
| Outlet              | If there are receivers in the transferred file, the program will automatically assign it to the catchment area. If there are none, the name of the generated catchment area will be assigned. |
| Area                | A parameter passed by the user.                                                                     |
| Percent Imperv      | Parameter calculated as described above and assigned to the catchment area.                          |
| Width               | The generated catchment areas are square in shape; therefore, the length of the side of the catchment area is assigned. |
| Percent Slope       | Parameter calculated as described above and assigned to the catchment area.                          |
| N-Imperv            | The value taken based on the linguistic variables passed to the fuzzy logic controller, which were previously mapped with Manning coefficients. |
| N-Perv              | The value taken based on the linguistic variables passed to the fuzzy logic controller, which were previously mapped with Manning coefficients. |
| Dstore-Imperv       | The value taken based on the linguistic variables passed to the fuzzy logic controller, which were previously mapped with typical storage values. |
| Dstore-Perv         | The value taken based on the linguistic variables passed to the fuzzy logic controller, which were previously mapped with typical storage values. |
| Percent Zero Imperv | The value taken based on the linguistic variables passed to the fuzzy logic controller, which were previously mapped with typical storage values. |
| RouteTo             | Odpływ z obszarów imperv i perv spływa bezpośrednio do wylotu.                                       |
| Coordinate          | Square-shaped catchments are generated, located so that one side is the edge of the contact.         |




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

License
This project is licensed under the [MIT License](https://github.com/BuczynskiRafal/rapid-catchment-generator/blob/main/LICENSE). By using, distributing, or contributing to this project, you agree to the terms and conditions of the license. Please refer to the [LICENSE.md](https://github.com/BuczynskiRafal/rapid-catchment-generator/blob/main/LICENSE) file for the full text of the license.