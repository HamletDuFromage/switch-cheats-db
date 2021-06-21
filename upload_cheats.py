#!/usr/bin/env python3

from bs4 import BeautifulSoup
import requests
import time
import datetime
import os
import rarfile
import zipfile
import shutil
import cloudscraper
import sys

from process_cheats import ProcessCheats

if __name__ == '__main__':
    scraper = cloudscraper.create_scraper()
    page = scraper.get("https://gbatemp.net/download/cheat-codes-sxos-and-ams-main-cheat-file-updated.36311/")

    soup = BeautifulSoup(page.content, "html.parser")

    dl_url = "https://gbatemp.net/" + soup.find("a", {"class": "inner"}).get("href")
    print(dl_url)

    version = dl_url.split("=")[1]

    if len(sys.argv) <= 1 or sys.argv[1] != version:
        print(f"New version available: {version}")
        with open("VERSION", 'w') as version_file:
            version_file.write(version)

        date = datetime.datetime.today()
        date_str = str(date).split()[0] + " - " + str(date.hour) + ":" + str(date.minute)

        with open("DATE", 'w') as date_file:
            date_file.write(date_str)

        dl = scraper.get(dl_url, allow_redirects=True)
        open("titles.rar", "wb").write(dl.content)

        correct_archive = False
        if rarfile.is_rarfile("titles.rar") :
            rf = rarfile.RarFile("titles.rar")
            rf.extractall()
            correct_archive = True
        elif zipfile.is_zipfile("titles.rar"):
            zf = zipfile.ZipFile("titles.rar")
            zf.extractall()
            correct_archive = True

        if correct_archive:
            shutil.make_archive("titles", "zip", base_dir="titles")
            os.rename("titles", "contents")
            shutil.make_archive("contents", "zip", base_dir="contents")
            ProcessCheats("contents", "cheats").parseCheats()
        else:
            print("Invalid archive")

    else:
        print(f"Cheats are already up to date at version: {version}")