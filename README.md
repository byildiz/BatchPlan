# BatchPlan

## About

BatchPlan as a robust large-scale floor plan extraction tool designed to be highly customizable, extensible, and pluggable in various capacities. The design decisions are meticulously crafted, particularly for the processing of extensive BIM data stored in IFC files.

## Installation

BatchPlan is dependent to [pythonocc-core](https://github.com/tpaviot/pythonocc-core) which is curretly only available as conda package. Thus we need to create a conda environment as follows:

First we need to copy [environment.yml](./environment.yml) to your machine and run the following command to create the environment with needed dependencies:

```
conda env create -f environment.yml
```

Now we need to install BatchPlan. There is two ways:

1. Installing with pip:

```
pip install BatchPlan
```

2. Building from source:

```
git clone https://github.com/byildiz/BatchPlan.git
cd BatchPlan
pip install .
```

## Usage

```
python -m batchplan.extract_floor_plans examples/data/Shependomlaan/IFC\ Schependomlaan.ifc --formatter FloorWKTFormatter --output output
```

## Known Issues and Limitations

- There is memory leakage which makes processing huge projects hard.
- BatchPlan currently can't run on a machine without a GUI environment.
