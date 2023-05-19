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
For the construction of the catchment generator, the type of land use was divided according to Table 1, 
the land cover according to Table 2. 
The categories were determined on the basis of the data presented by (Dołęga, Rogala, 1973), given below in Table 3. 

<h3 style="text-align: left;">Table 1. Land use categories</h3>
<table style="margin-left:auto; margin-right:auto; text-align:center;">
<thead>
<tr>
<th>Number</th>
<th>Land Use</th>
</tr>
</thead>
<tbody>
<tr>
<td>1</td>
<td>marshes and lowlands</td>
</tr>
<tr>
<td>2</td>
<td>flats and plateaus</td>
</tr>
<tr>
<td>3</td>
<td>flats and plateaus in combination with hills</td>
</tr>
<tr>
<td>4</td>
<td>hills with gentle slopes</td>
</tr>
<tr>
<td>5</td>
<td>steeper hills and foothills</td>
</tr>
<tr>
<td>6</td>
<td>hills and outcrops of mountain ranges</td>
</tr>
<tr>
<td>7</td>
<td>higher hills</td>
</tr>
<tr>
<td>8</td>
<td>mountains</td>
</tr>
<tr>
<td>9</td>
<td>highest mountains</td>
</tr>
</tbody>
</table>

<h3 style="text-align: left;">Table 2. Land cover categories</h3>
<table style="margin-left:auto; margin-right:auto; text-align:center;">
<thead>
<tr>
<th>Number</th>
<th>Land cover</th>
</tr>
</thead>
<tbody>
<tr>
<td>1</td>
<td>medium conditions</td>
</tr>
<tr>
<td>2</td>
<td>permeable areas</td>
</tr>
<tr>
<td>3</td>
<td>permeable terrain on plains</td>
</tr>
<tr>
<td>4</td>
<td>hilly</td>
</tr>
<tr>
<td>5</td>
<td>mountains</td>
</tr>
<tr>
<td>6</td>
<td>bare rocky slopes</td>
</tr>
<tr>
<td>7</td>
<td>urban</td>
</tr>
<tr>
<td>8</td>
<td>suburban</td>
</tr>
<tr>
<td>9</td>
<td>rural</td>
</tr>
<tr>
<td>10</td>
<td>forests</td>
</tr>
<tr>
<td>11</td>
<td>meadows</td>
</tr>
<tr>
<td>12</td>
<td>arable</td>
</tr>
<tr>
<td>13</td>
<td>marshes</td>
</tr>
</tbody></table>

<h3 style="text-align: left;">Table 3. Runoff coefficients o according to Iszkowski</h3>
<table style="margin-left:auto; margin-right:auto; text-align:center;">
<thead>
<tr>
<th>Number</th>
<th>Topographic terrain definition</th>
<th>Drainage coefficient ϕ</th>
</tr>
</thead>
<tbody>
<tr>
<td>1</td>
<td>marshes and lowlands</td>
<td>0.20</td>
</tr>
<tr>
<td>2</td>
<td>flats and plateaus</td>
<td>0.25</td>
</tr>
<tr>
<td>3</td>
<td>flats and plateaus in combination with hills</td>
<td>0.30</td>
</tr>
<tr>
<td>4</td>
<td>hills with gentle slopes</td>
<td>0.35</td>
</tr>
<tr>
<td>5</td>
<td>steeper hills and foothills</td>
<td>0.40</td>
</tr>
<tr>
<td>6</td>
<td>hills and outcrops of mountain ranges</td>
<td>0.45</td>
</tr>
<tr>
<td>7</td>
<td>higher hills</td>
<td>0.50</td>
</tr>
<tr>
<td>8</td>
<td>mountains</td>
<td>0.55</td>
</tr>
<tr>
<td>9</td>
<td>highest mountains</td>
<td>0.60-0.70</td>
</tr>
</tbody>
</table>

##
Table 4 shows what and how feature values are generated.
<h3 align="left">Table 4. SWMM catchment data.</h3>
<table align="center">
<thead>
<tr>
<th>Parameter name</th>
<th>Explanation</th>
</tr>
</thead>
<tbody>
<tr>
<td>Name</td>
<td>Catchment names (ID) are generated by adding a number.</td>
</tr>
<tr>
<td>Raingage</td>
<td>When "raingage exists in the uploaded file, it will be assigned to the catchment area being built. If it does not exist, it will be added to the file along with the "timeseries" and assigned to the catchment area being generated.</td>
</tr>
<tr>
<td>Outlet</td>
<td>If there are receivers in the transferred file, the program will automatically assign it to the catchment area, if there are none, the name of the generated catchment area will be assigned.</td>
</tr>
<tr>
<td>Area</td>
<td>A parameter passed by the user.</td>
</tr>
<tr>
<td>Percent Imperv</td>
<td>Parameter calculated as described above and assigned to the catchment area.</td>
</tr>
<tr>
<td>Width</td>
<td>The generated catchment areas are square in shape therefore the length of the side of the catchment area is assigned.</td>
</tr>
<tr>
<td>Percent Slope</td>
<td>Parameter calculated as described above and assigned to the catchment area.</td>
</tr>
<tr>
<td>N-Imperv</td>
<td>The value taken based on the linguistic variables passed to the fuzzy logic controller which were previously mapped with Manning coefficients.</td>
</tr>
<tr>
<td>N-Perv</td>
<td>The value taken based on the linguistic variables passed to the fuzzy logic controller which were previously mapped with Manning coefficients.</td>
</tr>
<tr>
<td>Dstore-Imperv</td>
<td>The value taken based on the linguistic variables passed to the fuzzy logic controller which were previously mapped with typical storage values.</td>
</tr>
<tr>
<td>Dstore-Perv</td>
<td>The value taken based on the linguistic variables passed to the fuzzy logic controller which were previously mapped with typical storage values.</td>
</tr>
<tr>
<td>Percent Zero Imperv</td>
<td>The value taken based on the linguistic variables passed to the fuzzy logic controller which were previously mapped with typical storage values.</td>
</tr>
<tr>
<td>RouteTo</td>
<td>Odpływ z obszarów imperv i perv spływa bezpośrednio do wylotu</td>
</tr>
<tr>
<td>Coordinate</td>
<td>Square-shaped catchments are generated, located so that one side is the edge of the contact.</td>
</tr>
</tbody>
</table>


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