## 2025-05-24 - [Unnecessary I/O in file generation]
**Learning:** In applications that generate thousands of small JSON files (20k+ in this case), the primary bottleneck is often disk I/O and OS filesystem metadata overhead. Comparing content before writing can save seconds of execution time even if some files must be updated.
**Action:** Always implement a "change-detection" check (either at the aggregate or individual level) before performing bulk file writes in scripts that run periodically.
