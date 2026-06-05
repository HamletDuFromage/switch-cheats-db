#!/usr/bin/env python3

import logging
import rarfile
import zipfile
import cloudscraper
import json
import shutil
from pathlib import Path
from datetime import date, datetime
from bs4 import BeautifulSoup
import os
from io import BytesIO
from urllib.parse import urljoin

import process_cheats
import re

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


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
        try:
            page = self.scraper.get(f"{self.page_url}/updates")
            soup = BeautifulSoup(page.content, "html.parser")
            candidates = []
            container = soup.find("div", {"class": "block-container"})
            if container:
                for t in container.find_all("time", {"class": "u-dt"}):
                    dt = t.get("datetime")
                    if dt:
                        try:
                            candidates.append(datetime.fromisoformat(dt))
                        except Exception:
                            pass
            if not candidates:
                for t in soup.select("time.u-dt"):
                    dt = t.get("datetime")
                    if dt:
                        try:
                            candidates.append(datetime.fromisoformat(dt))
                        except Exception:
                            pass
            if candidates:
                return max(candidates).date()
            logger.warning("Warning: unable to parse dates from GBAtemp updates page")
            return None
        except Exception as e:
            logger.error(f"Error fetching GBAtemp version: {e}")
            return None

    def has_new_cheats(self, database_version):
        try:
            return (self.gbatemp_version is not None) and (
                self.gbatemp_version > database_version
            )
        except Exception:
            return False

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
            logger.error(f"Error fetching repo info: {repo_info}")
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

    def download_archive(self, url, path, referer=None):
        headers = {}
        if referer:
            try:
                self.scraper.get(referer, allow_redirects=True, timeout=30)
            except Exception:
                pass
            headers["Referer"] = referer
        ua = getattr(self.scraper, "headers", {}).get("User-Agent")
        if ua:
            headers["User-Agent"] = ua
        headers["Accept"] = "*/*"
        headers["Accept-Language"] = "en-US,en;q=0.9"
        last_html = None
        for _ in range(3):
            resp = self.scraper.get(
                url, allow_redirects=True, headers=headers, timeout=60
            )
            content = resp.content
            buf = BytesIO(content)
            if zipfile.is_zipfile(buf) or rarfile.is_rarfile(buf):
                with open(path, "wb") as f:
                    f.write(content)
                return True
            try:
                soup = BeautifulSoup(content, "html.parser")
                last_html = content
                direct = None
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    if href.lower().endswith(".zip") or href.lower().endswith(".rar"):
                        direct = href
                        break
                if direct:
                    if direct.startswith("/"):
                        base = referer if referer else url
                        url = urljoin(base, direct)
                    else:
                        url = direct
                    continue
            except Exception:
                pass
            break
        if last_html:
            try:
                dbg_dir = Path("out")
                dbg_dir.mkdir(exist_ok=True)
                dbg_file = dbg_dir.joinpath(f"{Path(path).name}.html")
                with open(dbg_file, "wb") as f:
                    f.write(last_html)
            except Exception:
                pass
        logger.error("Download blocked or did not return an archive")
        return False

    def extract_archive(self, path, extract_path=None):
        if not Path(path).exists():
            logger.error(f"Archive not found: {path}")
            return False

        logger.info(f"Extracting {path} to {extract_path}...")

        if zipfile.is_zipfile(path):
            logger.info("Detected ZIP file.")
            try:
                zf = zipfile.ZipFile(path)
                zf.extractall(path=extract_path)
                logger.info("Extracted using zipfile.")
            except Exception as e:
                logger.error(f"zipfile extraction failed: {e}")
                return False
        elif rarfile.is_rarfile(path):
            logger.info("Detected RAR file.")
            try:
                rf = rarfile.RarFile(path)
                rf.extractall(path=extract_path)
                logger.info("Extracted using rarfile.")
            except rarfile.RarCannotExec:
                logger.warning("rarfile failed, trying patool")
                try:
                    import patoolib

                    os.environ["PATH"] = (
                        f"C:\\Program Files\\7-Zip;{os.environ.get('PATH','')}"
                    )

                    outdir = extract_path if extract_path else "."
                    if not Path(outdir).exists():
                        os.makedirs(outdir)
                    patoolib.extract_archive(str(path), outdir=str(outdir))
                    logger.info("Extracted using patool.")
                except Exception as e:
                    logger.error(f"patool extraction failed: {e}")
        else:
            logger.error("Unknown archive format")
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
            for key, bid in cheats.items():
                if key == "attribution":
                    continue
                if isinstance(bid, dict):
                    n_cheats += len(bid)
                    n_updates += 1
        n_games += 1

    stats_text = f"{n_cheats} cheats in {n_games} titles/{n_updates} updates"
    readme_file = Path("README.md")
    if not readme_file.exists():
        return

    content = readme_file.read_text(encoding="utf-8")
    pattern = r"<!-- STATS_START -->.*?<!-- STATS_END -->"
    replacement = f"<!-- STATS_START -->\n{stats_text}\n<!-- STATS_END -->"

    if re.search(pattern, content, re.DOTALL):
        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        readme_file.write_text(new_content, encoding="utf-8")
    else:
        # Fallback to old behavior if tags are missing
        lines = content.splitlines()
        if lines:
            lines[-1] = stats_text
            readme_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run():
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
            logger.info(f"Downloading cheats")
            ok = archive_worker.download_archive(
                gbatemp.get_download_url(), archive_path, referer=gbatemp.page_url
            )
            if ok:
                try:
                    archive_worker.extract_archive(archive_path, "gbatemp")
                except Exception as e:
                    logger.error(f"Failed to extract GBAtemp cheats: {e}")
                    Path("gbatemp/titles").mkdir(parents=True, exist_ok=True)
            else:
                logger.warning("Skipping extraction for GBAtemp due to blocked download")
                Path("gbatemp/titles").mkdir(parents=True, exist_ok=True)

            archive_worker.download_archive(highfps.get_download_url(), archive_path)
            try:
                archive_worker.extract_archive(archive_path)
            except Exception as e:
                logger.error(f"Failed to extract HighFPS cheats: {e}")
                Path("NX-60FPS-RES-GFX-Cheats-main/titles").mkdir(
                    parents=True, exist_ok=True
                )

            logger.info("Processing the cheat sheets")
            # Process each source once into its specific directory
            logger.info("Processing GBAtemp cheats...")
            process_cheats.ProcessCheats("gbatemp/titles", cheats_gba_path)
            logger.info("Processing HighFPS cheats...")
            process_cheats.ProcessCheats("NX-60FPS-RES-GFX-Cheats-main/titles", cheats_gfx_path)

            # Combine them into the main cheats directory more efficiently
            # Instead of re-parsing everything, we could just copy/merge the JSONs,
            # but ProcessCheats already handles merging if the files exist.
            # To avoid redundant work, we only need to call it once per source for the main path.
            logger.info("Merging into main cheats database...")
            process_cheats.ProcessCheats("gbatemp/titles", cheats_path)
            process_cheats.ProcessCheats("NX-60FPS-RES-GFX-Cheats-main/titles", cheats_path)

            logger.info("building complete cheat sheets")
            out_path = Path("complete")
            out_path.mkdir(exist_ok=True)
            archive_worker.build_cheat_files(cheats_path, out_path)

            logger.info("Creating the archives")
            archive_worker.create_archives("complete")
            archive_worker.create_archives("NX-60FPS-RES-GFX-Cheats-main")
            archive_worker.create_archives("gbatemp")

            archive_worker.create_version_file()

            count_cheats(cheats_path)

        else:
            logger.info("Everything is already up to date!")


if __name__ == "__main__":
    run()
