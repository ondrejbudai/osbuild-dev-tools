#!/usr/bin/python3
import argparse
import contextlib
import os
import subprocess
import tempfile
import urllib.request
from datetime import datetime


def read_file(path) -> str:
    with open(path) as f:
        return f.read()


def download_tarball(url: str, version: str, package: str) -> str:
    tarball_path = f"{package}-{version}.tar.gz"
    urllib.request.urlretrieve(
        f"{url}/archive/v{version}.tar.gz",
        tarball_path
    )

    return tarball_path


@contextlib.contextmanager
def extracted_tarball(path: str):
    with tempfile.TemporaryDirectory() as tempdir:
        subprocess.run(["tar", "-xf", path, "--directory", tempdir], check=True)
        yield tempdir


def merge_specfiles(downstream: str, upstream: str, version: str, author: str):
    down_lines = downstream.splitlines()
    up_lines = upstream.splitlines()

    changelog_start_in_down_spec = down_lines.index("%changelog")
    changelog_start_in_up_spec = up_lines.index("%changelog")

    date = datetime.now().strftime("%a %b %d %Y")

    changelog = f"""\
* {date} {author} - {version}-1
- New upstream release

"""

    merged_lines = up_lines[:changelog_start_in_up_spec + 1] + \
                   changelog.splitlines() + \
                   down_lines[changelog_start_in_down_spec + 1:]

    return "\n".join(merged_lines) + "\n"


def update_distgit(package: str, url: str, version: str, author: str, pkgtool: str):
    specfile = f"{package}.spec"

    # strip the ending /
    url = url.rstrip("/")
    upstream_project_name = url.split("/")[-1]

    tarball = download_tarball(url, version, package)

    old_downstream_specfile = read_file(specfile)

    with extracted_tarball(tarball) as path:
        new_upstream_specfile = read_file(f"{path}/{upstream_project_name}-{version}/{specfile}")

    new_downstream_specfile = merge_specfiles(old_downstream_specfile, new_upstream_specfile, version, author)

    with open(specfile, "w") as f:
        f.write(new_downstream_specfile)

    subprocess.check_call([pkgtool, "new-sources", tarball])
    subprocess.check_call(["git", "add", ".gitignore", specfile, "sources"])
    subprocess.check_call(["git", "commit", "-m", f"Update to {version}"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--package", metavar="STRING", type=str, help="package name downstream", required=True)
    parser.add_argument("--url", metavar="URL", type=str, help="github url of the project", required=True)
    parser.add_argument("--distgit-checkout", metavar="DIR", type=str, help="distgit local checkout", required=True)
    parser.add_argument("--version", metavar="VERSION", type=str, help="version to be released to downstream",
                        required=True)
    parser.add_argument("--author", metavar="VERSION", type=str,
                        help="author of the downstream change (format: Name Surname <email@example.com>", required=True)
    parser.add_argument("--pkgtool", metavar="PKGTOOL", type=str, help="fedpkg or rhpkg", required=True)
    args = parser.parse_args()

    if args.pkgtool not in ["fedpkg", "rhpkg"]:
        raise RuntimeError("--pkgtool must be fedpkg or rhpkg!")

    os.chdir(args.distgit_checkout)

    update_distgit(
        args.package,
        args.url,
        args.version,
        args.author,
        args.pkgtool
    )
