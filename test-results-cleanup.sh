#!/bin/bash

# one script that covers cleanup for all possible tests

# only in the models directory

# these are tla and cfg models that are generated, and are then removed
find models -name "*.tla" -type f -exec rm -i {} \;
find models -name "cfg.tla" -type f -exec rm -i {} \;
find models -name "out.tla" -type f -exec rm -i {} \;

