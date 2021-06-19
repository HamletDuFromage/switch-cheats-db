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
        if self.changed:
            self.writeMasterFiles()
            self.writeTitleFiles()

    def loadVersionFile(self):
        self.data = json.loads(requests.get(self.url).text.upper())

    def getVersionDict(self):
        for tid in self.data:
            if(tid[:13] + "000") not in self.versions_dict:
                self.versions_dict[tid[:13] + "000"] = {}
            for ver in self.data[tid]:
                if("BUILDID" in self.data[tid][ver]["CONTENTENTRIES"][0]):
                    self.versions_dict[tid[:13] + "000"][str(self.data[tid][ver]["VERSION"])] = self.data[tid][ver]["CONTENTENTRIES"][0]["BUILDID"][:16]

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
            json.dump(self.versions_dict, json_file, indent = 4)
        with open(self.cbor_path, 'wb') as cbor_file:
            json_out = json.dumps(self.versions_dict)
            cbor2.dump(json_out, cbor_file)
        print(f"Updated master {self.json_path} and {self.cbor_path}")

    def writeTitleFiles(self):
        if not(os.path.exists(self.dir_path)):
            os.mkdir(self.dir_path)

        for tid in self.versions_dict:
            path = f"{self.dir_path}{tid}.json"
            change = False
            if os.path.exists(path):
                with open(path, 'r') as json_file:
                    old = json.load(json_file)
                if old != self.versions_dict[tid]:
                    change = True
            else:
                change = True
            if change:
                with open(path, 'w') as json_file:
                    json.dump(self.versions_dict[tid], json_file, indent = 4)
                    print(f"Updated {path}")

if __name__ == '__main__':
    ProcessVersions("https://raw.githubusercontent.com/blawar/titledb/master/cnmts.json").updateVersions()