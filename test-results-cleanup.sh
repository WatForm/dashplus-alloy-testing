#!/bin/bash

# one script that covers cleanup for all possible tests

# only in the models directory

# these are tla and cfg models that are generated, and are then removed
find models -name "*.tla" -type f -exec rm -i {} \;
find models -name "*.cfg" -type f -exec rm -i {} \;
find models -name "*.tlc" -type f -exec rm -i {} \;
find models -name "*.out" -type f -exec rm -i {} \;

# we need to remove all folders named /states/ as well
# it might be easier to just delete everything ignored by git?
