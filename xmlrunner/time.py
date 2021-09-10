"""Timing function that will attempt to circumvent freezegun and other common
techniques of mocking time in Python unit tests; will only succeed at this on
Unix currently. Falls back to regular time.time().
"""

import time

def get_real_time_if_possible():
    if hasattr(time, 'clock_gettime'):
        try:
            return time.clock_gettime(time.CLOCK_REALTIME)
        except OSError:
            # would occur if time.CLOCK_REALTIME is not available, for example
            pass
    return time.time()
