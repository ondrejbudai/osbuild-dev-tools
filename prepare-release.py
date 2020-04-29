#!/usr/bin/python3
import argparse
import contextlib
import os
import subprocess
import tempfile
import urllib.request


def read_file(path) -> str:
    with open(path) as f:
        return f.read()


def download_tarball(url: str, version: int) -> str:
    tarball_path = f"osbuild-composer-{version}.tar.gz"
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


def merge_specfiles(downstream: str, upstream: str):
    down_lines = downstream.splitlines()
    up_lines = upstream.splitlines()

    changelog_start_in_down_spec = down_lines.index("%changelog")
    changelog_start_in_up_spec = up_lines.index("%changelog")

    merged_lines = up_lines[:changelog_start_in_up_spec] + down_lines[changelog_start_in_down_spec:]

    return "\n".join(merged_lines) + "\n"


def main(package: str, url: str, version: int):
    # strip the ending /
    url = url.rstrip("/")
    upstream_project_name = url.split("/")[-1]

    tarball = download_tarball(url, version)

    old_downstream_specfile = read_file(f"{package}.spec")

    with extracted_tarball(tarball) as path:
        new_upstream_specfile = read_file(f"{path}/{upstream_project_name}-{version}/{package}.spec")

    new_downstream_specfile = merge_specfiles(old_downstream_specfile, new_upstream_specfile)

    with open(f"{package}.spec", "w") as f:
        f.write(new_downstream_specfile)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scm", metavar="PATH", type=str, help="scm directory path", required=True)
    parser.add_argument("--package", metavar="STRING", type=str, help="the fedora package name", required=True)
    parser.add_argument("--url", metavar="URL", type=str, help="the github url of the project", required=True)
    parser.add_argument("--version", metavar="VERSION", type=int, help="the next version", required=True)
    args = parser.parse_args()
    os.chdir(f"{args.scm}/{args.package}")
    main(
        args.package,
        args.url,
        args.version,
    )
