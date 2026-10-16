# Consumer V2 preflight corrections before NEW neural heads

- The first finite-ticket fixture contained a single valid completion and
  failed its branch-count assertion. Adding whitespace exercised the full law
  before the successful six-oracle preflight; no law failure was relabeled.
- The first model-free native-service preflight failed with AttributeError:
  Python3.11's time module does not expose clock_getcpuclockid (it exposes the
  different pthread helper). The CPU service was closed by the constructor's
  exception handler. Zero actual model forwards occurred. The corrected
  accessor calls POSIX clock_getcpuclockid through libc with explicit ctypes
  argument/return types, then reads that clock with time.clock_gettime.
  The pthread function is not called with a process ID.

These are preflight failures, not neural latency data or publication evidence.
