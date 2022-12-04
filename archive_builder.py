#!/usr/bin/env python3

from pathlib import Path
import shutil
import json
from datetime import date


def build_archive(cheats_path, out_path):
    cheats_path = Path(cheats_path)
    titles_path = Path(out_path).joinpath("titles")
    if not(titles_path.exists()):
        titles_path.mkdir(parents=True)
    for tid in cheats_path.iterdir():
        tid_path = titles_path.joinpath(tid.stem)
        tid_path.mkdir()
        with open(tid, "r") as cheats_file:
            cheats_dict = json.load(cheats_file)
        for key, value in cheats_dict.items():
            if key == "attribution":
                for author, content in value.items():
                    with open(tid_path.joinpath(author), "w") as attribution_file:
                        attribution_file.write(content)
            else:
                cheats = ""
                for cheat in value:
                    cheats += cheat["content"]
                with open(tid_path.joinpath(f"{key}.txt"), "w") as bid_file:
                    bid_file.write(cheats)
    shutil.make_archive(str(titles_path.resolve()), "zip", base_dir=titles_path)
    contents_path = titles_path.rename(titles_path.parent.joinpath("contents"))
    shutil.make_archive(str(contents_path.resolve()), "zip", base_dir=contents_path)

def create_version_file(out_path):
    with open(f"{out_path}/VERSION", "w") as version_file:
        version_file.write(str(date.today()))

build_archive("cheats", "out")
create_version_file("out")




