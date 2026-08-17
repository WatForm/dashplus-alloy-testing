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

# contain macros
rmfiles.append(Path("../models/alloy-tools-models/simple-models/4-bit-adder/4-bit-adder.als"))
rmfiles.append(Path("../models/alloy-tools-models/models/logic/philosophers.als"))
rmfiles.append(Path("../models/alloy-tools-models/puzzles/8-queens/queens.als"))
rmfiles.append(Path("../models/alloy-tools-models/puzzles/coloring/color-australia.als"))
rmfiles.append(Path("../models/alloy-tools-models/puzzles/einstein/einstein-wikipedia.als"))
rmfiles.append(Path("../models/alloy-tools-models/utilities/time/overlapping-ranges.als"))

rmfiles.append(Path("../models/eid-day-expert-models/expert-models/5x4l2fj5nfbq3cz2dumwdt57g3kig3rd-litmustestgen/tso_perturbed.als"))
rmfiles.append(Path("../models/eid-day-expert-models/expert-models/5x4l2fj5nfbq3cz2dumwdt57g3kig3rd-litmustestgen/c11_perturbed.als"))
rmfiles.append(Path("../models/eid-day-expert-models/expert-models/5x4l2fj5nfbq3cz2dumwdt57g3kig3rd-litmustestgen/power_perturbed.als"))
rmfiles.append(Path("../models/eid-day-expert-models/expert-models/5x4l2fj5nfbq3cz2dumwdt57g3kig3rd-litmustestgen/scc_perturbed_scflip.als"))
rmfiles.append(Path("../models/eid-day-expert-models/expert-models/gumxtrzzbkrtwi7jtwyu7eibi3fwhgmf-models/simple-models/4-bit-adder/4-bit-adder.als"))
rmfiles.append(Path("../models/eid-day-expert-models/expert-models/gumxtrzzbkrtwi7jtwyu7eibi3fwhgmf-models/puzzles/8-queens/queens.als"))
rmfiles.append(Path("../models/eid-day-expert-models/expert-models/gumxtrzzbkrtwi7jtwyu7eibi3fwhgmf-models/models/logic/philosophers.als"))
rmfiles.append(Path("../models/eid-day-expert-models/expert-models/gumxtrzzbkrtwi7jtwyu7eibi3fwhgmf-models/puzzles/coloring/color-australia.als"))
rmfiles.append(Path("../models/eid-day-expert-models/expert-models/gumxtrzzbkrtwi7jtwyu7eibi3fwhgmf-models/utilities/time/overlapping-ranges.als"))
rmfiles.append(Path("../models/eid-day-expert-models/expert-models/x7t75qqe5fr6uzitot5sdu63o7drnur5-TransForm/tso_transistency_perturbed.als"))
rmfiles.append(Path("../models/eid-day-expert-models/expert-models/x7t75qqe5fr6uzitot5sdu63o7drnur5-TransForm/util/tso_transistency_perturbed_minimality_check.al"))
rmfiles.append(Path("../models/eid-day-expert-models/expert-models/x7t75qqe5fr6uzitot5sdu63o7drnur5-TransForm/util/tso_transistency_perturbed_minimize.als"))
rmfiles.append(Path("../models/eid-day-expert-models/expert-models/x7t75qqe5fr6uzitot5sdu63o7drnur5-TransForm/util/tso_transistency_perturbed_minimality_check.als"))


for f in rmfiles:
    try:
        os.remove(f)
    except FileNotFoundError:
        pass