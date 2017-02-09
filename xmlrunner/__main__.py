"""Main entry point"""

import sys
from .unittest import TestProgram
from .runner import XMLTestRunner

if sys.argv[0].endswith("__main__.py"):
    import os.path
    # We change sys.argv[0] to make help message more useful
    # use executable without path, unquoted
    # (it's just a hint anyway)
    # (if you have spaces in your executable you get what you deserve!)
    executable = os.path.basename(sys.executable)
    sys.argv[0] = executable + " -m xmlrunner"
    del os

__unittest = True

# Default output to '.' may be changed by the --xmloutput param
output='.'
if '--xmloutput' in sys.argv:
    i = sys.argv.index('--xmloutput')
    del sys.argv[i]
    try:
        output=sys.argv[i]
        if output.startswith('-'):
            raise IndexError
        del sys.argv[i]
    except IndexError:
        sys.exit('Missing output for the --xmloutput param.')

main = TestProgram

main(
    module=None, testRunner=XMLTestRunner(output=output),
    # see issue #59
    failfast=False, catchbreak=False, buffer=False)
