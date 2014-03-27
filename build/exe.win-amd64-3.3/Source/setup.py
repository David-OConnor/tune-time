import sys
import os

import cx_Freeze

import module_locator

#includes = ['sip', 'scipy.signal', 'scipy.optimize.nonlin',
        #        'matplotlib.backends.backend_tkagg']

#includes = ['sip', 'matplotlib.backends.backend_tkagg']
includes = ['sip']
DIR = module_locator.path()
base = "Win32GUI" if sys.platform == "win32" else None
#base = None

cx_Freeze.setup(
    name = "TuneTime",
    version = "0.1",
    description = "Tunes and times",
    options = {'build_exe': {'includes': includes}},
    executables = [cx_Freeze.Executable(os.path.join(DIR, 'tune_time.pyw'),
                   base=base, icon=os.path.join(DIR, 'icon.ico'))]
)
