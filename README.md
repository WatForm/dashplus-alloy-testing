# Testing Directory for dashplus Alloy Functionality

# TL;DR

`./setup.sh` (download all model sets and do other set up)  
`cd testing-scripts`  
`python3 test_aa_dp_parse_resolve.py` (test if dashplus parsing and resolving passes on models in two smaller model-sets that pass parse/resolve of AA6.2)

# Requirements

* bash, python3, wget, unzip, git, sed
* **jenv is used to set version of java in directories (currently java 17.0.16 and 25 are required)**
* dashplus repo is in a **sister directory**

# Setup

./setup.sh 
to download models, libs, compile java programs
it is safe to run this multiple times as it will not redownload models and libs if they are present

./complete-cleanup.sh 
to wipe put all downloads and intermediate files

./test-results-cleanup.sh 
to wipe out test results only

# Binaries (lib/)

The setup.sh script wgets/git clones any binaries needed for testing.
**dashplus is symbolically linked to a sister directory.**

# Model Sets (models/)

After setup, the models directory contains: 

1) ../models/alloy-tools-models 
* ~100 models from https://github.com/AlloyTools/models
* util files are removed (on setup) b/c they cause a circular dependency on integer.als in AA6.2 when they are parsed by themselves
* all models pass AA6.2 parse/resolve

2) catalyst-corpus/catalyst-corpus-fail 
* ~40000 models
* downloaded from a dashplus-alloy-testing release
of .als models scraped from the web in Oct 2025
* they all fail AA6.2 parse/resolve

3) catalyst-corpus/catalyst-corpus-pass 
* ~38000 models
* downloaded from a dashplus-alloy-testing release
of .als models scraped from the web in Oct 2025
* they all pass AA6.2 parse/resolve

4) eid-day-expert-models 
* 95 models
* downloaded from a dashplus-alloy-testing release
of .als models 
* they all pass AA6.2 parse/resolve

There are no duplicate .als files within catalyst-corpus or between catalyst-corpus and alloytools/models and eid-day-expert-models. There are a few duplicate .als files between alloytools/models and eid-day-expert-models because these are previously curated model sets)

There are script files models/remove-unsupported-X.py, which can be run to remove certains models that are not supported by some part of the process for a documented reason.

## Tests (testing-scripts/)

See testing-scripts/README.md


## Extra notes (for mac o/s)

* to count files in a directory
`find . -type f -name "*.als" | wc -l`

* to interactively choose which duplicates to keep
`jdupes -r -d .`

* to find duplicates
`fdupes -r -d .`

* to create a zip file without dot files and system files
`zip -r archive.zip archive -x "*/.*" -x ".*" -x "__MACOSX/*" -x "*.DS_Store"`

