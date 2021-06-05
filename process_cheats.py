#!/usr/bin/env python3

from os import mkdir, listdir, path
from string import hexdigits
from pathlib import Path
import re
import subprocess
import json

#find contents -depth -exec rename 's/(.*)\/([^\/]*)/$1\/\U$2/' {} \;

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
        #print(json.dumps(out))
        return out

    def constructBidDict(self, tid, sheet):
        in_sheet = f"{self.in_path}/{tid}/CHEATS/{sheet}"
        out = []
        pos = []
        try:
            with open(in_sheet, 'r', encoding="utf-8", errors="ignore") as cheatSheet:
                lines = cheatSheet.readlines()

            for i in range(len(lines)):
                title = re.search("(\[.+\])", lines[i])
                if title:
                    pos.append(i)
                    out.append({"title": title[0]})

            for i in range(len(pos) - 1):
                out[i]["content"] = "".join(lines[pos[i]:pos[i + 1]])
            out[-1]["content"] = "".join(lines[pos[-1]:])
        except IndexError:
            print(f"error: IndexError in {in_sheet}")
        return out

    def createJson(self, tid):
        out_sheet = f"{self.out_path}/{tid}.json"
        out = self.constructCheatDict(tid)
        change = False
        if path.exists(out_sheet):
            with open(out_sheet, 'r') as json_file:
                old = json.load(json_file)
            if(json.dumps(old)) != json.dumps(out):
                change = True
        else:
            change = True
        if change:
            with open(out_sheet, 'w') as json_file:
                json.dump(out, json_file, indent = 4)
            print(f"{out_sheet} has been modified")

    def parseCheats(self):
        subprocess.call(['bash', '-c', f"find {self.in_path} -depth -exec rename 's/(.*)\\/([^\\/]*)/$1\\/\\U$2/' {{}} \\;"])
        if not(Path(self.out_path).is_dir()):
            mkdir(self.out_path)
        tids = listdir(self.in_path)
        for tid in tids:
            if self.isHexAnd16Char(tid):
                self.createJson(tid)