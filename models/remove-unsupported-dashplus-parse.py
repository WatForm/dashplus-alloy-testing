"""
    This script removes expert models that use features Portus doesn't/won't support.
    This is done in Python rather than bash to support Windows and Linux pathnames.
"""

import os
from pathlib import Path 

rmfiles = []

# use X$.subfields (part of Alloy's meta-modelling facility)
rmfiles.append(Path("../models/eid-day-expert-models/expert-models/3zltn65gds66b6f4q3lvbtgdkb6snmuu-alloy/hc-atd/hc7.als"))
rmfiles.append(Path("../models/eid-day-expert-models/expert-models/gumxtrzzbkrtwi7jtwyu7eibi3fwhgmf-models/puzzles/einstein/einstein-wikipedia.als"))




for f in rmfiles:
    try:
        os.remove(f)
    except FileNotFoundError:
        pass