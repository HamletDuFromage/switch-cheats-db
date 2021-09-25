#!/usr/bin/env python3

from os import mkdir, listdir, path
from string import hexdigits
from pathlib import Path
import re
import subprocess
import json


class ProcessCheats:
    def __init__(self, in_path, out_path):
        self.out_path = out_path
        self.in_path = in_path

    def isHexAnd16Char(self, file_name):
        return (len(file_name) == 16) and (all(c in hexdigits for c in file_name[0:15]))

    def constructCheatDict(self, tid):
        out = {}
        try:
            cheatSheets = listdir(f"{self.in_path}/{tid}/CHEATS/")
            for sheet in cheatSheets:
                if self.isHexAnd16Char(sheet[:-4]):
                    out[sheet[:-4]] = self.constructBidDict(tid, sheet)
        except FileNotFoundError:
            print(f"error: FileNotFoundError in {tid}")
            pass
        return out

    def constructBidDict(self, tid, sheet):
        in_sheet = f"{self.in_path}/{tid}/CHEATS/{sheet}"
        out = []
        pos = []
        try:
            with open(in_sheet, 'r', encoding="utf-8", errors="ignore") as cheatSheet:
                lines = cheatSheet.readlines()

            for i in range(len(lines)):
                titles = re.search("(\[.+\]|\{.+\})", lines[i])
                if titles:
                    pos.append(i)

            for i in range(len(pos) - 1):
                code = "".join(lines[pos[i]:pos[i + 1]])
                if pos[i + 1] - pos[i] > 1 and re.search("[0-9a-fA-F]{8}", code):
                    out.append({"title": lines[pos[i]].strip(),
                                "content": code})
            out.append({"title": lines[pos[-1]].strip(),
                        "content": "".join(lines[pos[-1]:])})
        except IndexError:
            print(f"error: IndexError in {in_sheet}")
        return out

    def checkForChanges(self, path, cheats_dict):
        try:
            with open(path, 'r') as read_file:
                old = json.load(read_file)
            if old != cheats_dict:
                print(f"{path} changed")
                return True
        except FileNotFoundError:
            print(f"File {path} doesn't exist, creating it")
            return True
        return False

    def createJson(self, tid):
        out_sheet = f"{self.out_path}/{tid.upper()}.json"
        out = self.constructCheatDict(tid)
        if self.checkForChanges(out_sheet, out):
            with open(out_sheet, 'w') as json_file:
                json.dump(out, json_file, indent=4)

    def parseCheats(self):
        subprocess.call(['bash', '-c', f"chmod -R +rw {self.in_path}"])
        subprocess.call(
            ['bash', '-c', f"find {self.in_path} -depth -exec rename 's/(.*)\\/([^\\/]*)/$1\\/\\U$2/' {{}} \\;"])
        # subprocess.call(['bash', '-c', f"find {self.in_path} -depth -exec perl-rename 's/(.*)\\/([^\\/]*)/$1\\/\\U$2/' {{}} \\;"])
        if not(Path(self.out_path).is_dir()):
            mkdir(self.out_path)
        tids = listdir(self.in_path)
        for tid in tids:
            if self.isHexAnd16Char(tid):
                self.createJson(tid)


if __name__ == '__main__':
    ProcessCheats("contents", "cheats").parseCheats()
