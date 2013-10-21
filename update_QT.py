import os

import module_locator


DIR = module_locator.path()
os.system(' '.join(['pyuic5', os.path.join(DIR, 'tune_time.ui'), '>', os.path.join(DIR, 'tuner_gui.py')]))
os.system(' '.join(['pyuic5', os.path.join(DIR, 'about.ui'), '>', os.path.join(DIR, 'about_gui.py')]))
#os.system(' '.join(['pyuic5', os.path.join(DIR, 'settings.ui'), '>', os.path.join(DIR, 'settings_gui.py')]))
os.system(' '.join(['pyuic5', os.path.join(DIR, 'hotkeys.ui'), '>', os.path.join(DIR, 'hotkeys_gui.py')]))

os.system(' '.join(['pyrcc5', os.path.join(DIR, 'tuner.qrc'), '-o', os.path.join(DIR, 'tuner_rc.py')]))
