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
    def __init__(self, archive_path="titles.rar", old_version="-1", new_version="-1"):
        self.archive_path = archive_path
        self.old_version = old_version
        self.version = new_version
        self.page_url = "https://gbatemp.net/download/cheat-codes-sxos-and-ams-main-cheat-file-updated.36311/"
        self.dl_url = ""
        self.scraper = cloudscraper.create_scraper()
        self.fetchUrl()

    def downloadAndExtract(self):
        if self.writeVersion():
            self.downloadArchive()
            self.extractArchive()

    def fetchUrl(self):
        page = self.scraper.get(self.page_url)
        soup = BeautifulSoup(page.content, "html.parser")
        self.dl_url = f"{self.page_url}download"
        self.version = self.compareVersions(soup.find("ol", {"class": "block-body"}).find(
            "div").getText(), soup.find("span", {"class": "u-muted"}).getText())
        print(f"version: {self.version}")

    def compareVersions(self, date1, date2):
        res = date1[4:7] >= date2[4:7] and date1[0:1] >= date2[0:1] and date1[2:3] >= date2[2:3]
        if res:
            return date1
        else:
            return date2

    def writeVersion(self):
        if self.old_version != self.version:
            print(f"New version available: {self.version}")
            with open("VERSION", 'w') as version_file:
                version_file.write(self.version)

            date = datetime.datetime.today()
            date_str = str(date).split()[0] + " - " + \
                str(date.hour) + ":" + str(date.minute)

            with open("DATE", 'w') as date_file:
                date_file.write(date_str)
            return True
        else:
            print(f"No update available at version: {self.version}")
            return False

    def downloadArchive(self):
        dl = self.scraper.get(self.dl_url, allow_redirects=True)
        open(self.archive_path, "wb").write(dl.content)

    def extractArchive(self):
        correct_archive = False
        if rarfile.is_rarfile(self.archive_path):
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
    requiredNamed.add_argument(
        '-a', '--archive', help='archive path', required=False, default='titles.rar')
    requiredNamed.add_argument(
        '-o', '--old_version', help='previous version', required=False, default='-1')
    requiredNamed.add_argument(
        '-n', '--new_version', help='new version', required=False, default='-1')
    args = parser.parse_args()
    uploader = UploadCheats(archive_path=args.archive,
                            old_version=args.old_version, new_version=args.new_version)
    uploader.downloadAndExtract()
    # uploader.fetchUrl()
