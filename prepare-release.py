#!/usr/bin/python3
import argparse
import contextlib
import os
import subprocess
import tempfile
from os import path


@contextlib.contextmanager
def chdir(path: str):
    old_cwd = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(old_cwd)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", metavar="STRING", type=str, help="package name downstream", required=True)
    parser.add_argument("--url", metavar="URL", type=str, help="github url of the project", required=True)
    parser.add_argument("--distgit", metavar="URL", type=str, help="distgit clone url", required=True)
    parser.add_argument("--version", metavar="VERSION", type=int, help="version to be released to downstream",
                        required=True)
    parser.add_argument("--author", metavar="VERSION", type=str,
                        help="author of the downstream change (format: Name Surname <email@example.com>", required=True)
    parser.add_argument("--release", metavar="VERSION", type=str, help="distribution release (f33, f32, master)",
                        required=True)
    parser.add_argument("--pkgtool", metavar="PKGTOOL", type=str, help="fedpkg or rhpkg", required=True)
    args = parser.parse_args()

    if args.pkgtool not in ["fedpkg", "rhpkg"]:
        raise RuntimeError("--pkgtool must be fedpkg or rhpkg!")

    with tempfile.TemporaryDirectory() as temp_dir:
        dir = path.join(temp_dir, args.package)

        subprocess.check_call(["git", "clone", args.distgit, dir])
        subprocess.check_call(["git", "-C", dir, "checkout", args.release])

        dirname = os.path.dirname(os.path.abspath(__file__))
        cmd = os.path.join(dirname, 'update-distgit.py')
        print()
        subprocess.check_call([
            cmd,
            "--package", args.package,
            "--url", args.url,
            "--distgit-checkout", dir,
            "--version", str(args.version),
            "--author", args.author,
            "--pkgtool", args.pkgtool
        ])

        with chdir(dir):
            subprocess.check_call([args.pkgtool, "scratch-build", "--srpm"])
            # subprocess.check_call(["git", "push"])
            # subprocess.check_call([args.pkgtool, "build"])
