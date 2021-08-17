#!/usr/bin/env python3

from bs4 import BeautifulSoup
from pathlib import Path
import argparse
import datetime
import os
import rarfile
import zipfile
import shutil
import cloudscraper

from process_cheats import ProcessCheats

class UploadCheats:
    def __init__(self, old_version, archive_path = "titles.rar"):
        self.archive_path = archive_path
        self.old_version = old_version
        self.version = "0"
        self.dl_url = ""
        self.scraper = cloudscraper.create_scraper()
        self.fetchUrl()
        self.downloadArchive()
        self.extractArchive()

    def fetchUrl(self):
        page = self.scraper.get("https://gbatemp.net/download/cheat-codes-sxos-and-ams-main-cheat-file-updated.36311/")
        soup = BeautifulSoup(page.content, "html.parser")
        self.dl_url = "https://gbatemp.net/" + soup.find("a", {"class": "inner"}).get("href")
        self.version = self.dl_url.split("=")[1]
        print(self.dl_url)

    def downloadArchive(self):
        if self.old_version != self.version:
            print(f"New version available: {self.version}")
            with open("VERSION", 'w') as version_file:
                version_file.write(self.version)

            date = datetime.datetime.today()
            date_str = str(date).split()[0] + " - " + str(date.hour) + ":" + str(date.minute)

            with open("DATE", 'w') as date_file:
                date_file.write(date_str)

            dl = self.scraper.get(self.dl_url, allow_redirects=True)
            open(self.archive_path, "wb").write(dl.content)

    def extractArchive(self):
        correct_archive = False
        if rarfile.is_rarfile(self.archive_path) :
            rf = rarfile.RarFile(self.archive_path)
            rf.extractall()
            correct_archive = True
        elif zipfile.is_zipfile(self.archive_path):
            zf = zipfile.ZipFile(self.archive_path)
            zf.extractall()
            correct_archive = True

        if correct_archive:
            shutil.make_archive("titles", "zip", base_dir="titles")
            os.rename("titles", "contents")
            shutil.make_archive("contents", "zip", base_dir="contents")
            ProcessCheats("contents", "cheats").parseCheats()
        else:
            print("Invalid archive")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Update the cheats database")
    requiredNamed = parser.add_argument_group('arguments')
    requiredNamed.add_argument('-a', '--archive', help='archive path', required=False, default='titles.rar')
    requiredNamed.add_argument('-v', '--version', help='previous version', required=False, default="-1")
    args = parser.parse_args()
    uploader = UploadCheats(args.version, args.archive)