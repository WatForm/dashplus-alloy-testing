#!/bin/bash

# clean up all setup

cd models
rm -rf alloy-tools-models
rm -rf catalyst-corpus
rm -rf eid-day-expert-models
cd ..

cd libs
rm -rf *
cd ..

cd testing-scripts
rm -rf __pycache__
rm -rf *.class
cd ..

./test-results-cleanup.sh 
