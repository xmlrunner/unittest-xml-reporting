# -*- coding: utf-8 -*-

"""
This module provides the XMLTestRunner class, which is heavily based on the
default TextTestRunner.
"""

# Allow version to be detected at runtime.
try:
    from .version import __version__
except ImportError:
    __version__ = "unknown"

from .runner import XMLTestRunner

__all__ = ('__version__', 'XMLTestRunner')
