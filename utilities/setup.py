import sys
import os

import cx_Freeze

import module_locator

#includes = ['sip', 'scipy.signal', 'scipy.optimize.nonlin',
        #        'matplotlib.backends.backend_tkagg']

#includes = ['sip', 'matplotlib.backends.backend_tkagg']
name = 'tune_time'
includes = ['sip']
DIR = module_locator.path()
DIR_PY = os.path.abspath(os.path.join(DIR, os.pardir, name))
DIR_RES = os.path.abspath(os.path.join(DIR, os.pardir, 'resources'))
base = "Win32GUI" if sys.platform == "win32" else None

cx_Freeze.setup(
    name = name,
    version = "0.1",
    description = "Tunes and times",
    options = {'build_exe': {'includes': includes}},
    executables = [cx_Freeze.Executable(os.path.join(DIR_PY, name+'.pyw'),
                   path = DIR_PY, base=base, icon=os.path.join(DIR_RES, 'icon.ico'))]
)
