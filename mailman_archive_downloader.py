#!/usr/bin/env python3
import configparser
import logging
import os.path
import sys
from timeit import default_timer as timer
from urllib.parse import urljoin

import requests.auth
from bs4 import BeautifulSoup

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

DEBUG = False


def download_mailman_archive(session, user, password, url):
    print("Loading url", url, "...")

    resp = session.post(url, data={"username": user, "password": password})

    # resp = session.get(url)
    resp.raise_for_status()

    print("Done")
    html_content = resp.text

    if DEBUG:
        with open("mailman_archive_index.html", "w") as f:
            f.write(html_content)

    soup = BeautifulSoup(html_content, "lxml")
    all_archive_links = soup.find_all(
        "a", attrs={"href": lambda v: v.strip().endswith("txt.gz")}
    )
    for archive_fn in [l.attrs["href"] for l in all_archive_links]:
        archive_url = urljoin(url, archive_fn)
        print("Download", archive_url, "...")
        resp = session.get(archive_url)
        resp.raise_for_status()
        print("Downloaded", len(resp.content), "bytes")
        output_fn = archive_fn[: -len(".txt.gz")] + ".mbox"
        print("Write to file", output_fn)
        with open(output_fn, "wb") as f:
            f.write(resp.content)


if __name__ == "__main__":
    cfg_file = "config.ini"
    if not os.path.isfile(cfg_file):
        print("Error: Configuration file", cfg_file, "not found", file=sys.stderr)
        sys.exit(1)
    cfg_parser = configparser.ConfigParser()
    cfg_parser.read(cfg_file)
    user = cfg_parser.get("mailman", "user", fallback=None)
    if user is None:
        print(
            "Error: user is not specified in configuration file",
            cfg_file,
            file=sys.stderr,
        )
        sys.exit(1)
    password = cfg_parser.get("mailman", "password", fallback=None)
    if password is None:
        print(
            "Error: password is not specified in configuration file",
            cfg_file,
            file=sys.stderr,
        )
        sys.exit(1)
    url = cfg_parser.get("mailman", "url", fallback=None)
    if url is None:
        print(
            "Error: url is not specified in configuration file",
            cfg_file,
            file=sys.stderr,
        )
        sys.exit(1)

    start = timer()

    with requests.Session() as s:
        download_mailman_archive(s, user, password, url)

    end = timer()
    hours, rem = divmod(end - start, 3600)
    minutes, seconds = divmod(rem, 60)
    print(
        "Elapsed time: {:0>2}:{:0>2}:{:05.2f}".format(int(hours), int(minutes), seconds)
    )
