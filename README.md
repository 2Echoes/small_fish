# Small Fish
**Small Fish** is a python application for the analysis of smFish images. It provides a ready to use graphical interface to combine famous python packages for cell analysis without any need for coding.

Cell segmentation is peformed using *cellpose* (published work) : https://github.com/MouseLand/cellpose

Spot detection is performed via big-fish (published work) : https://github.com/fish-quant/big-fish

Time stacks are not yet supported.

## Installation

It is higly recommanded to create a specific [conda](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html) or [virtual](https://docs.python.org/3.6/library/venv.html) environnement to install small fish.

```bash
conda create -n small_fish python=3.8
activate bigfish_env
```
Then download the package

## Run Small fish

First activate your python environnement : 
```bash
activate bigfish_env
```
Then launch Small fish : 
```bash
python -m small_fish
```
## Developpement

Optional features to include in future versions : 
- batch processing
- time stack (which would include cell tracking)
- 3D segmentation
