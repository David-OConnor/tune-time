import module_locator
import os

DIR = module_locator.path()
os.system(' '.join(['python', os.path.join(DIR, 'setup.py'), 'build']))
