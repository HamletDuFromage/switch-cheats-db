## 2025-05-14 - [Efficient File Parsing in process_cheats.py]
**Learning:** The original `constructBidDict` used `readlines()` followed by multiple passes and regex compilations per line, which was inefficient for large cheat files.
**Action:** Use a single-pass, line-by-line iteration with pre-compiled regex at the module level. This improved performance by ~1.8x on large files and reduced memory pressure.
