#!/usr/bin/env python3

import json
import cbor2
import requests
import os


class ProcessVersions:
    def __init__(self, cnmts_url, titles_url):
        self.json_path = "versions.json"
        self.cbor_path = "versions.cbor"
        self.dir_path = "versions/"
        self.changed = False
        self.versions_dict = dict()
        self.data = dict()
        try:
            self.data = json.loads(requests.get(cnmts_url).text)
        except ValueError:
            print("Invalid JSON file!")
        self.title_dict = self.create_names_dict(titles_url)

    def update_versions(self):
        if self.data:
            self.get_version_dict()
            self.check_for_changes()
            self.write_master_files()
            self.write_title_files()

    def get_version_dict(self):
        for tid in self.data:
            tid_base = tid[:13].upper() + "000"
            if (tid_base) not in self.versions_dict:
                self.versions_dict[tid_base] = {}
                try:
                    self.versions_dict[tid_base]["title"] = self.title_dict[tid_base]
                except KeyError:
                    pass

            latest_ver = 0
            for ver in self.data[tid]:
                if "buildId" in self.data[tid][ver]["contentEntries"][0]:
                    self.versions_dict[tid_base][str(self.data[tid][ver]["version"])
                                                                 ] = self.data[tid][ver]["contentEntries"][0]["buildId"][:16].upper()
                latest_ver = max(latest_ver, int(ver))
            self.versions_dict[tid_base]["latest"] = latest_ver

    def check_for_changes(self):
        try:
            with open(self.json_path, 'r') as read_file:
                old = json.load(read_file)
            if old != self.versions_dict:
                self.changed = True
                print(f"{self.json_path} changed")
        except FileNotFoundError:
            print("File doesn't exist")
            self.changed = True

    def write_master_files(self):
        with open(self.json_path, 'w') as json_file:
            json.dump(self.versions_dict, json_file, indent=4, sort_keys=True)
        """ with open(self.cbor_path, 'wb') as cbor_file:
            cbor2.dump(json.dumps(self.versions_dict), cbor_file) """

    def write_title_files(self):
        if not(os.path.exists(self.dir_path)):
            os.mkdir(self.dir_path)

        for tid in self.versions_dict:
            path = f"{self.dir_path}{tid}.json"
            with open(path, 'w') as json_file:
                json.dump(
                    self.versions_dict[tid], json_file, indent=4, sort_keys=True)

    def create_names_dict(self, url):
        out = dict()
        for key, value in json.loads(requests.get(url).text).items():
            out[value["id"]] = value["name"]
        return out


if __name__ == '__main__':
    processor = ProcessVersions("https://raw.githubusercontent.com/blawar/titledb/master/cnmts.json", "https://raw.githubusercontent.com/blawar/titledb/master/US.en.json")
    processor.update_versions()
