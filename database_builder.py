#!/usr/bin/env python3

import rarfile
import zipfile
import cloudscraper
import json
import shutil
from pathlib import Path
from datetime import date, datetime
from bs4 import BeautifulSoup
import os

import process_cheats
import re


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
        page = self.scraper.get(f"{self.page_url}/updates")
        soup = BeautifulSoup(page.content, "html.parser")
        dates = soup.find("div", {"class": "block-container"}).find_all(
            "time", {"class": "u-dt"}
        )
        version = max([datetime.fromisoformat(date.get("datetime")) for date in dates])
        return version.date()

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
        token = os.getenv("GITHUB_TOKEN")
        headers = {}
        if token:
            headers["Authorization"] = f"token {token}"
        repo_info = self.scraper.get(self.api_url, headers=headers).json()
        if "commit" not in repo_info:
            print(f"Error fetching repo info: {repo_info}")
        last_commit_date = (
            repo_info.get("commit").get("commit").get("author").get("date")
        )
        return date.fromisoformat(last_commit_date.split("T")[0])

    def has_new_cheats(self, database_version):
        return self.highfps_version > database_version

    def get_high_FPS_version(self):
        return self.highfps_version

    def get_download_url(self):
        return self.download_url


class ArchiveWorker:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper()

    def sanitize_name(self, name: str) -> str:
        return re.sub(r'[<>:"/\\|?*]', "_", name).strip()

    def download_archive(self, url, path):
        dl = self.scraper.get(url, allow_redirects=True)
        open(path, "wb").write(dl.content)

    def extract_archive(self, path, extract_path=None):
        if rarfile.is_rarfile(path):
            try:
                rf = rarfile.RarFile(path)
                rf.extractall(path=extract_path)
            except rarfile.RarCannotExec:
                print("rarfile failed, trying patool")
                try:
                    import patoolib
                except ImportError:
                    return False
                outdir = extract_path if extract_path else "."
                if not os.path.exists(outdir):
                    os.makedirs(outdir)
                try:
                    patoolib.extract_archive(str(path), outdir=str(outdir))
                except Exception:
                    return False
        elif zipfile.is_zipfile(path):
            zf = zipfile.ZipFile(path)
            zf.extractall(path=extract_path)
        else:
            return False
        return True

    def build_cheat_files(self, cheats_path, out_path):
        cheats_path = Path(cheats_path)
        titles_path = Path(out_path).joinpath("titles")
        if not (titles_path.exists()):
            titles_path.mkdir(parents=True)
        for tid in cheats_path.iterdir():
            tid_path = titles_path.joinpath(tid.stem)
            tid_path.mkdir(exist_ok=True)
            with open(tid, "r", encoding="utf-8") as cheats_file:
                cheats_dict = json.load(cheats_file)
            for key, value in cheats_dict.items():
                if key == "attribution":
                    for author, content in value.items():
                        safe_name = self.sanitize_name(author)
                        with open(
                            tid_path.joinpath(safe_name), "w", encoding="utf-8"
                        ) as attribution_file:
                            attribution_file.write(content)
                else:
                    cheats_folder = tid_path.joinpath("cheats")
                    cheats_folder.mkdir(exist_ok=True)
                    cheats = ""
                    for _, content in value.items():
                        cheats += content
                    if cheats:
                        with open(
                            cheats_folder.joinpath(f"{key}.txt"), "w", encoding="utf-8"
                        ) as bid_file:
                            bid_file.write(cheats)

    def touch_all(self, path):
        for path in path.rglob("*"):
            if path.is_file():
                path.touch()

    def create_archives(self, out_path):
        out_path = Path(out_path)
        titles_path = out_path.joinpath("titles")
        self.touch_all(titles_path)
        shutil.make_archive(
            str(titles_path.resolve()), "zip", root_dir=out_path, base_dir="titles"
        )
        target_contents = titles_path.parent.joinpath("contents")
        if target_contents.exists():
            shutil.rmtree(target_contents)
        shutil.copytree(titles_path, target_contents)
        contents_path = target_contents
        self.touch_all(contents_path)
        shutil.make_archive(
            str(contents_path.resolve()), "zip", root_dir=out_path, base_dir="contents"
        )

    def create_version_file(self, out_path="."):
        with open(f"{out_path}/VERSION", "w") as version_file:
            version_file.write(str(date.today()))


def count_cheats(cheats_directory):
    n_games = 0
    n_updates = 0
    n_cheats = 0
    for json_file in Path(cheats_directory).glob("*.json"):
        with open(json_file, "r", encoding="utf-8") as file:
            cheats = json.load(file)
            for bid in cheats.values():
                n_cheats += len(bid)
                n_updates += 1
        n_games += 1

    readme_file = Path("README.md")
    with readme_file.open("r", encoding="utf-8") as file:
        lines = file.readlines()
    lines[-1] = f"{n_cheats} cheats in {n_games} titles/{n_updates} updates"
    with readme_file.open("w", encoding="utf-8") as file:
        file.writelines(lines)


if __name__ == "__main__":
    cheats_path = "cheats"
    cheats_gba_path = "cheats_gbatemp"
    cheats_gfx_path = "cheats_gfx"
    archive_path = "titles.zip"
    database = DatabaseInfo()
    database_version = database.get_database_version()
    highfps = HighFPSCheatsInfo()
    gbatemp = GbatempCheatsInfo()
    if gbatemp.has_new_cheats(database_version) or highfps.has_new_cheats(
        database_version
    ):
        archive_worker = ArchiveWorker()
        print(f"Downloading cheats")
        archive_worker.download_archive(gbatemp.get_download_url(), archive_path)
        try:
            archive_worker.extract_archive(archive_path, "gbatemp")
        except Exception as e:
            print(f"Failed to extract GBAtemp cheats: {e}")
            Path("gbatemp/titles").mkdir(parents=True, exist_ok=True)

        archive_worker.download_archive(highfps.get_download_url(), archive_path)
        try:
            archive_worker.extract_archive(archive_path)
        except Exception as e:
            print(f"Failed to extract HighFPS cheats: {e}")
            Path("NX-60FPS-RES-GFX-Cheats-main/titles").mkdir(
                parents=True, exist_ok=True
            )

        print("Processing the cheat sheets")
        process_cheats.ProcessCheats("gbatemp/titles", cheats_gba_path)
        process_cheats.ProcessCheats(
            "NX-60FPS-RES-GFX-Cheats-main/titles", cheats_gfx_path
        )
        process_cheats.ProcessCheats(
            "gbatemp/titles", cheats_path
        )  # this could be done more elegantly
        process_cheats.ProcessCheats("NX-60FPS-RES-GFX-Cheats-main/titles", cheats_path)

        print("building complete cheat sheets")
        out_path = Path("complete")
        out_path.mkdir(exist_ok=True)
        archive_worker.build_cheat_files(cheats_path, out_path)

        print("Creating the archives")
        archive_worker.create_archives("complete")
        archive_worker.create_archives("NX-60FPS-RES-GFX-Cheats-main")
        archive_worker.create_archives("gbatemp")

        archive_worker.create_version_file()

        count_cheats(cheats_path)

    else:
        print("Everything is already up to date!")
