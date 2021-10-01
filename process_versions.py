#!/usr/bin/env python3

import json
import cbor2
import requests
import os


class ProcessVersions:
    def __init__(self, url):
        self.url = url
        self.data = {}
        self.versions_dict = {}
        self.json_path = "versions.json"
        self.cbor_path = "versions.cbor"
        self.dir_path = "versions/"
        self.changed = False

    def updateVersions(self):
        self.loadVersionFile()
        self.getVersionDict()
        self.checkForChanges()
        self.writeMasterFiles()
        self.writeTitleFiles()

    def loadVersionFile(self):
        self.data = json.loads(requests.get(self.url).text)

    def getVersionDict(self):
        for tid in self.data:
            if (tid[:13].upper() + "000") not in self.versions_dict:
                self.versions_dict[tid[:13].upper() + "000"] = {}
            for ver in self.data[tid]:
                if "buildId" in self.data[tid][ver]["contentEntries"][0]:
                    self.versions_dict[tid[:13].upper() + "000"][str(self.data[tid][ver]["version"])
                                                                 ] = self.data[tid][ver]["contentEntries"][0]["buildId"][:16].upper()

    def checkForChanges(self):
        try:
            with open(self.json_path, 'r') as read_file:
                old = json.load(read_file)
            if old != self.versions_dict:
                self.changed = True
                print(f"{self.json_path} changed")
        except FileNotFoundError:
            print("File doesn't exist")
            self.changed = True

    def writeMasterFiles(self):
        with open(self.json_path, 'w') as json_file:
            json.dump(self.versions_dict, json_file, indent=4, sort_keys=True)
        """ with open(self.cbor_path, 'wb') as cbor_file:
            cbor2.dump(json.dumps(self.versions_dict), cbor_file) """

    def writeTitleFiles(self):
        if not(os.path.exists(self.dir_path)):
            os.mkdir(self.dir_path)

        for tid in self.versions_dict:
            path = f"{self.dir_path}{tid}.json"
            with open(path, 'w') as json_file:
                json.dump(
                    self.versions_dict[tid], json_file, indent=4, sort_keys=True)


if __name__ == '__main__':
    ProcessVersions(
        "https://raw.githubusercontent.com/blawar/titledb/master/cnmts.json").updateVersions()
