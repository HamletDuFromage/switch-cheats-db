#!/usr/bin/env python3

import rarfile
import zipfile
import cloudscraper
import json
import shutil
from pathlib import Path
from datetime import date
from bs4 import BeautifulSoup

import process_cheats


def version_parser(version):
    year = int(version[4:8])
    month = int(version[0:2])
    day = int(version[2:4])
    return date(year, month, day)


class DatabaseInfo:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper()
        self.database_version_url = "https://github.com/HamletDuFromage/switch-cheats-db/releases/latest/download/VERSION"
        self.database_version = self.fetch_database_version()

    def fetch_database_version(self):
        version = self.scraper.get(self.database_version_url).text
        return date.fromisoformat(version)

    def get_database_version(self):
        return self.database_version


class GbatempCheatsInfo:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper()
        self.page_url = "https://gbatemp.net/download/cheat-codes-sxos-and-ams-main-cheat-file-updated.36311/"
        self.gbatemp_version = self.fetch_gbatemp_version()

    def fetch_gbatemp_version(self):
        page = self.scraper.get(self.page_url)
        soup = BeautifulSoup(page.content, "html.parser")
        # There are two occurances of the version, we pick the biggest one
        version1 = version_parser(soup.find("ol", {"class": "block-body"}).find("div").getText())
        version2 = version_parser(soup.find("span", {"class": "u-muted"}).getText())
        return max(version1, version2)

    def has_new_cheats(self, database_version):
        return self.gbatemp_version > database_version

    def get_gbatemp_version(self):
        return self.gbatemp_version

    def get_download_url(self):
        return f"{self.page_url}/download"


class HighFPSCheatsInfo:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper()
        self.download_url = "https://github.com/ChanseyIsTheBest/NX-60FPS-RES-GFX-Cheats/archive/refs/heads/main.zip"
        self.api_url = "https://api.github.com/repos/ChanseyIsTheBest/NX-60FPS-RES-GFX-Cheats/branches/main"
        self.highfps_version = self.fetch_high_FPS_cheats_version()

    def fetch_high_FPS_cheats_version(self):
        repo_info = self.scraper.get(self.api_url).json()
        last_commit_date = repo_info.get("commit").get("commit").get("author").get("date")
        return date.fromisoformat(last_commit_date.split("T")[0])

    def has_new_cheats(self, database_version):
        return self.highfps_version > database_version

    def get_high_FPS_version(self):
        return self.highfps_version

    def get_download_url(self):
        return self.download_url


class ArchiveWorker():
    def __init__(self):
        self.scraper = cloudscraper.create_scraper()

    def download_archive(self, url, path):
        dl = self.scraper.get(url, allow_redirects=True)
        open(path, "wb").write(dl.content)

    def extract_archive(self, path, extract_path=None):
        if rarfile.is_rarfile(path):
            rf = rarfile.RarFile(path)
            rf.extractall(path=extract_path)
        elif zipfile.is_zipfile(path):
            zf = zipfile.ZipFile(path)
            zf.extractall(path=extract_path)
        else:
            return False
        return True

    def build_cheat_files(self, cheats_path, out_path):
        cheats_path = Path(cheats_path)
        titles_path = Path(out_path).joinpath("titles")
        if not(titles_path.exists()):
            titles_path.mkdir(parents=True)
        for tid in cheats_path.iterdir():
            tid_path = titles_path.joinpath(tid.stem)
            tid_path.mkdir()
            with open(tid, "r") as cheats_file:
                cheats_dict = json.load(cheats_file)
            for key, value in cheats_dict.items():
                if key == "attribution":
                    for author, content in value.items():
                        with open(tid_path.joinpath(author), "w") as attribution_file:
                            attribution_file.write(content)
                else:
                    cheats = ""
                    for cheat, content in value.items():
                        cheats += content
                    if cheats:
                        with open(tid_path.joinpath(f"{key}.txt"), "w") as bid_file:
                            bid_file.write(cheats)

    def create_archives(self, out_path, quantifier=""):
        out_path = Path(out_path)
        titles_path = out_path.joinpath("titles")
        if quantifier:
            quantifier = f"({quantifier})"
        shutil.make_archive(str(titles_path.resolve()), "zip", root_dir=out_path, base_dir="titles")
        titles_path
        contents_path = titles_path.rename(titles_path.parent.joinpath("contents"))
        shutil.make_archive(str(contents_path.resolve()), "zip", root_dir=out_path, base_dir="contents")

    def create_version_file(self, out_path="."):
        with open(f"{out_path}/VERSION", "w") as version_file:
            version_file.write(str(date.today()))

if __name__ == '__main__':
    cheats_path = "cheats"
    cheats_gba_path = "cheats_gbatemp"
    cheats_gfx_path = "cheats_gfx"
    archive_path = "titles.zip"
    database = DatabaseInfo()
    database_version = database.get_database_version()
    highfps = HighFPSCheatsInfo()
    gbatemp = GbatempCheatsInfo()
    if gbatemp.has_new_cheats(database_version) or highfps.has_new_cheats(database_version):
    #if True:
        archive_worker = ArchiveWorker()
        print(f"Downloading cheats")
        archive_worker.download_archive(gbatemp.get_download_url(), archive_path)
        archive_worker.extract_archive(archive_path, "gbatemp")
        archive_worker.download_archive(highfps.get_download_url(), archive_path)
        archive_worker.extract_archive(archive_path)

        print("Processing the cheat sheets")
        process_cheats.ProcessCheats("gbatemp/titles", cheats_gba_path)
        process_cheats.ProcessCheats("NX-60FPS-RES-GFX-Cheats-main/titles", cheats_gfx_path)
        process_cheats.ProcessCheats("gbatemp/titles", cheats_path) # this could be done more elegantly
        process_cheats.ProcessCheats("NX-60FPS-RES-GFX-Cheats-main/titles", cheats_path)

        print("building complete cheat sheets")
        out_path = Path("complete")
        out_path.mkdir()
        archive_worker.build_cheat_files(cheats_path, out_path)

        print("Creating the archives")
        archive_worker.create_archives("complete")
        archive_worker.create_archives("NX-60FPS-RES-GFX-Cheats-main")
        archive_worker.create_archives("gbatemp")

        archive_worker.create_version_file()

    else:
        print("Everything is already up to date!")
