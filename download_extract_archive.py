#!/usr/bin/env python3

import rarfile
import zipfile
import cloudscraper
from datetime import date
from bs4 import BeautifulSoup


def versionParser(version):
    year = int(version[4:8])
    month = int(version[0:2])
    day = int(version[2:4])
    return date(year, month, day)


class DatabaseInfo:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper()
        self.database_version_url = "https://github.com/HamletDuFromage/switch-cheats-db/releases/latest/download/VERSION"
        self.database_version = self.fetchDatabaseVersion()

    def fetchDatabaseVersion(self):
        version = self.scraper.get(self.database_version_url).text
        return date.fromisoformat(version)

    def getDatabaseVersion(self):
        return self.database_version


class GbatempCheatsInfo:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper()
        self.page_url = "https://gbatemp.net/download/cheat-codes-sxos-and-ams-main-cheat-file-updated.36311/"
        self.gbatemp_version = self.fetchGbatempVersion()

    def fetchGbatempVersion(self):
        page = self.scraper.get(self.page_url)
        soup = BeautifulSoup(page.content, "html.parser")
        # There are two occurances of the version, we pick the biggest one
        version1 = versionParser(soup.find("ol", {"class": "block-body"}).find("div").getText())
        version2 = versionParser(soup.find("span", {"class": "u-muted"}).getText())
        return max(version1, version2)

    def hasNewCheats(self, database_version):
        return self.gbatemp_version > database_version

    def getGbatempVersion(self):
        return self.gbatemp_version

    def getDownloadUrl(self):
        return f"{self.page_url}/download"


class HighFPSCheatsInfo:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper()
        self.download_url = "https://github.com/karmicpumpkin/NX-60FPS-RES-GFX-Cheats/archive/refs/heads/main.zip"
        self.api_url = "https://api.github.com/repos/karmicpumpkin/NX-60FPS-RES-GFX-Cheats/branches/main"
        self.highfps_version = self.fetchHighFPSCheatsVersion()

    def fetchHighFPSCheatsVersion(self):
        repo_info = self.scraper.get(self.api_url).json()
        last_commit_date = repo_info.get("commit").get("commit").get("author").get("date")
        return date.fromisoformat(last_commit_date.split("T")[0])

    def hasNewCheats(self, database_version):
        return self.highfps_version > database_version

    def getHighFPSVersion(self):
        return self.highfps_version

    def getDownloadUrl(self):
        return self.download_url


class DownloadExtractArchive():
    def __init__(self):
        self.scraper = cloudscraper.create_scraper()

    def downloadArchive(self, url, path):
        dl = self.scraper.get(url, allow_redirects=True)
        open(path, "wb").write(dl.content)

    def extractArchive(self, path):
        if rarfile.is_rarfile(path):
            rf = rarfile.RarFile(path)
            rf.extractall()
        elif zipfile.is_zipfile(path):
            zf = zipfile.ZipFile(path)
            zf.extractall()
        else:
            return False
        return True


if __name__ == '__main__':
    archive_path = "titles.zip"
    database = DatabaseInfo()
    database_version = database.getDatabaseVersion()
    highfps = HighFPSCheatsInfo()
    gbatemp = GbatempCheatsInfo()
    if gbatemp.hasNewCheats(database_version) or highfps.hasNewCheats(database_version):
        extractor = DownloadExtractArchive()
        for url in (highfps.getDownloadUrl(), gbatemp.getDownloadUrl()):
            extractor.downloadArchive(url, archive_path)
            extractor.extractArchive(archive_path)
