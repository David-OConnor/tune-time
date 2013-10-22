import os

import module_locator

name = 'tune_time' # Program name

DIR = module_locator.path()
DIR_PY = os.path.abspath(os.path.join(DIR, os.pardir, name))
DIR_RES = os.path.abspath(os.path.join(DIR, os.pardir, 'resources'))

os.system(' '.join(['pyuic5', os.path.join(DIR_RES, name+'.ui'), '>',
    os.path.join(DIR_PY, name+'_gui.py')]))
os.system(' '.join(['pyuic5', os.path.join(DIR_RES, 'about.ui'), '>',
    os.path.join(DIR_PY, 'about_gui.py')]))
#os.system(' '.join(['pyuic5', os.path.join(DIR, 'settings.ui'), '>',
    #os.path.join(DIR, 'settings_gui.py')]))
os.system(' '.join(['pyuic5', os.path.join(DIR_RES, 'hotkeys.ui'), '>',
    os.path.join(DIR_PY, 'hotkeys_gui.py')]))

os.system(' '.join(['pyrcc5', os.path.join(DIR_RES, name+'.qrc'),'-o',
    os.path.join(DIR_PY, name+'_rc.py')]))
