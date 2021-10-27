#!/usr/bin/env python3

import sys
import json
import re

with open("versions.json", "r") as versions_file:
    versions = json.load(versions_file)

for line in sys.argv:
    try:
        tid = re.search("/(.+)\.", line).group(1)
        if "title" in versions[tid]:
            print(versions[tid]["title"])
        else:
            print(tid)
    except (TypeError, AttributeError):
        pass
