# -*- coding: utf-8 -*-

"""
This module provides the XMLTestRunner class, which is heavily based on the
default TextTestRunner.
"""

import logging
try:
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())

# Allow version to be detected at runtime.
from .version import __version__

from .runner import XMLTestRunner

__all__ = ('__version__', 'XMLTestRunner')
