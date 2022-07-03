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

    def getCheatsPath(self, tid):
        folder_path = f"{self.in_path}/{tid}"
        folders = listdir(folder_path)
        for folder in folders:
            if folder.lower() == "cheats":
                return f"{folder_path}/{folder}"
        return ""

    def constructCheatDict(self, tid):
        out = {}
        folder_path = self.getCheatsPath(tid)
        try:
            cheatSheets = listdir(folder_path)
            for sheet in cheatSheets:
                if self.isHexAnd16Char(sheet[:-4]):
                    out[sheet[:-4].upper()] = self.constructBidDict(f"{folder_path}/{sheet}")
        except FileNotFoundError:
            print(f"error: FileNotFoundError {folder_path}")
        return out

    def constructBidDict(self, sheet_path):
        out = []
        pos = []
        with open(sheet_path, 'r', encoding="utf-8", errors="ignore") as cheatSheet:
            lines = cheatSheet.readlines()

        for i in range(len(lines)):
            titles = re.search("(\[.+\]|\{.+\})", lines[i])
            if titles:
                pos.append(i)

        for i in range(len(pos)):
            try:
                codeLines = lines[pos[i]:pos[i + 1]]
            except IndexError:
                codeLines = lines[pos[i]:]
            if len(codeLines) > 1:
                code = "".join(codeLines)
                if re.search("[0-9a-fA-F]{8}", code):
                    out.append({"title": lines[pos[i]].strip(),
                                "content": code})
        return out

    def createJson(self, tid):
        out_sheet = f"{self.out_path}/{tid.upper()}.json"
        out = self.constructCheatDict(tid)
        with open(out_sheet, 'w') as json_file:
            json.dump(out, json_file, indent=4, sort_keys=True)

    def parseCheats(self):
        subprocess.call(['bash', '-c', f"chmod -R +rw {self.in_path}"])
        if not(Path(self.out_path).is_dir()):
            mkdir(self.out_path)
        tids = listdir(self.in_path)
        for tid in tids:
            if self.isHexAnd16Char(tid):
                self.createJson(tid)


if __name__ == '__main__':
    ProcessCheats("contents", "cheats").parseCheats()
