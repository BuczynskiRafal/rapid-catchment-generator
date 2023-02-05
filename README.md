# README
Tool for rapid prototyping of a hydraulic model that can be read and edited with SWMM.

## Requirements
* Python 3

## Usage
To run the script, use the following command: 
```python3 main.py file_path``` 
where `file_path` is the path to the SWMM model file.


## About
For the construction of the catchment generator, the type of land use was divided according to Table 1, 
the landform according to Table 2. 
The categories were determined on the basis of the data presented by (Dołęga, Rogala, 1973), given below in Table 3. 

### Table 1: Land use categories	
| Number  | Land Use                                     |
|---------|----------------------------------------------|
| 1       | marshes and lowlands                         |
| 2       | flats and plateaus                           |
| 3       | flats and plateaus in combination with hills |
| 4       | hills with gentle slopes                     |
| 5       | steeper hills and foothills                  |
| 6       | hills and outcrops of mountain ranges        |
| 7       | higher hills                                 |
| 8       | mountains                                    |
| 9       | highest mountains                            |



### Table 2 Landform categories	
| Number | Landform                    |
|--------|-----------------------------|
| 1      | medium conditions           |
| 2      | permeable areas             |
| 3      | permeable terrain on plains |
| 4      | hilly                       |
| 5      | mountains                   |
| 6      | bare rocky slopes           |
| 7      | urban                       |
| 8      | suburban                    |
| 9      | rural                       |
| 10     | forests                     |
| 11     | meadows                     |
| 12     | arable                      |
| 13     | marshes                     |



### Table 3. Runoff coefficients o according to Iszkowski
 
| Land Use 	      | Flat (%) 	   	   | Slope (%)   	   | 
|-----------------|-------------------|--------------------| 
| Urban           | 80                | 20                 | 
| Forest          | 10                | 90                 |

### Table 3. Runoff coefficients o according to Iszkowski

| Number | Topographic terrain definition  | Drainage coefficient ϕ |
|------|---------------------------------|----------------------|
| 1    | marshes and lowlands                         | 0.20                 |
| 2    | flats and plateaus                           | 0.25                 |
| 3    | flats and plateaus in combination with hills | 0.30                 |
| 4    | hills with gentle slopes                     | 0.35                 |
| 5    | steeper hills and foothills                  | 0.40                 |
| 6    | hills and outcrops of mountain ranges        | 0.45                 |
| 7    | higher hills                                 | 0.50                 |
| 8    | mountains                                    | 0.55                 |
| 9    | highest mountains                            | 0.60-0.70            |


