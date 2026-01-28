#!/usr/bin/env python3

from os import mkdir, listdir, path
import os
from string import hexdigits
from pathlib import Path
import re
import subprocess
import json
from collections import OrderedDict


class ProcessCheats:
    def __init__(self, in_path, out_path):
        self.out_path = Path(out_path)
        self.in_path = Path(in_path)
        self.parseCheats()

    def isHexAnd16Char(self, file_name):
        return (len(file_name) == 16) and (all(c in hexdigits for c in file_name[0:15]))

    def getCheatsPath(self, tid):
        for folder in tid.iterdir():
            if folder.name.lower() == "cheats":
                return folder
        return None

    def getAttribution(self, tid):
        attribution = OrderedDict()
        for f in tid.iterdir():
            if f.suffix.lower() == ".txt":
                with open(
                    f, "r", encoding="utf-8", errors="ignore"
                ) as attribution_file:
                    attribution[f.name] = attribution_file.read()
        return attribution

    def constructBidDict(self, sheet_path):
        out = OrderedDict()
        pos = []
        with open(sheet_path, "r", encoding="utf-8", errors="ignore") as cheatSheet:
            lines = cheatSheet.readlines()

        for i in range(len(lines)):
            titles = re.search(r"(\[.+\]|\{.+\})", lines[i])
            if titles:
                pos.append(i)

        for i in range(len(pos)):
            try:
                codeLines = lines[pos[i] : pos[i + 1]]
            except IndexError:
                codeLines = lines[pos[i] :]
            if len(codeLines) > 1:
                code = "".join(codeLines)
                if re.search("[0-9a-fA-F]{8}", code):
                    out[lines[pos[i]].strip()] = code.strip("\n ") + "\n\n"
        return out

    def update_dict(self, new, old):
        for key, value in new.items():
            if key in old:
                old[key] |= value
            else:
                old[key] = value
        return old

    def createJson(self, tid):
        out = OrderedDict()
        cheats_dir = self.getCheatsPath(tid)
        if cheats_dir:
            cheats_file = self.out_path.joinpath(f"{tid.name.upper()}.json")
            prev = {}
            try:
                with open(cheats_file, "r", encoding="utf-8") as json_file:
                    prev = json.load(json_file)
            except FileNotFoundError:
                prev = {}
            prev_attr = prev.get("attribution", {})
            try:
                for sheet in cheats_dir.iterdir():
                    if self.isHexAnd16Char(sheet.stem):
                        out[sheet.stem.upper()] = self.constructBidDict(sheet)
            except FileNotFoundError:
                print(f"error: FileNotFoundError {folder_path}")
            new_attr = self.getAttribution(tid)
            # favor colon form over underscore form for attribution keys
            canon_new_attr = OrderedDict()
            for k, v in new_attr.items():
                k_colon = re.sub(r"_(?=\s)", ":", k)
                # if previous JSON already has the colon variant, use it
                key_final = k_colon if k_colon in prev_attr or ":" in k else k
                canon_new_attr[key_final] = v
            if new_attr:
                out = self.update_dict(out, {"attribution": canon_new_attr})
            # merge previous JSON, handling attribution explicitly to avoid duplicates
            if prev:
                merged = OrderedDict()
                # other keys
                for k, v in prev.items():
                    if k != "attribution":
                        merged = self.update_dict(merged, {k: v})
                # merge attribution
                combined_attr = OrderedDict()
                for k, v in prev_attr.items():
                    combined_attr[k] = v
                if "attribution" in out:
                    for k, v in out["attribution"].items():
                        combined_attr[k] = v
                # drop underscore variants if colon variant exists
                for k in list(combined_attr.keys()):
                    if "_" in k:
                        k_colon = re.sub(r"_(?=\s)", ":", k)
                        if k_colon in combined_attr:
                            del combined_attr[k]
                if combined_attr:
                    merged["attribution"] = combined_attr
                out = self.update_dict(out, merged)

            out = OrderedDict(sorted(out.items()))

            with open(cheats_file, "w", encoding="utf-8") as json_file:
                json.dump(out, json_file, indent=4)

    def parseCheats(self):
        if os.name != "nt":
            try:
                subprocess.call(["bash", "-c", f"chmod -R +rw {self.in_path}"])
            except FileNotFoundError:
                pass
            except Exception as e:
                print(f"Error changing permissions: {e}")

        if not (self.out_path.exists()):
            self.out_path.mkdir()
        for tid in self.in_path.iterdir():
            if self.isHexAnd16Char(tid.name):
                self.createJson(tid)
