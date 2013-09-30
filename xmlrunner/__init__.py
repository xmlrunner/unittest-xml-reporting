from runner import *

VERSION = (2, 0, 0)

def get_version():
    """Returns VERSION as string in X.Y.Z format.
    """
    return '.'.join(str(part) for part in VERSION)
