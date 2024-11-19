import tarfile
import zipfile
from argparse import ArgumentParser
from pathlib import Path
from shutil import copy, copytree, rmtree
from subprocess import run

import requests
from git import Repo
from github import Github

base = Path(__file__).parent


def cascadia():
    work_path = base / "cascadia-work"
    zip_path = base / "cascadia.zip"
    tar_path = base / "cascadia.tar.gz"
    dst_path = base / "cascadia-mono"

    if work_path.exists():
        rmtree(work_path)

    gh = Github()
    repo = gh.get_repo("microsoft/cascadia-code")
    release = repo.get_latest_release()

    if not zip_path.exists():
        with open(zip_path, "wb") as f:
            [asset] = release.assets
            f.write(requests.get(asset.browser_download_url).content)

    work_path.mkdir()
    with zipfile.ZipFile(zip_path) as f:
        f.extractall(work_path)

    if dst_path.exists():
        rmtree(dst_path)
    dst_path.mkdir()

    for p in (work_path / "otf" / "static").iterdir():
        if not p.stem.startswith("CascadiaMono-"):
            continue
        copy(p, dst_path / p.name)

    zip_path.unlink()
    rmtree(work_path)

    if not tar_path.exists():
        with open(tar_path, "wb") as f:
            f.write(requests.get(release.tarball_url).content)

    work_path.mkdir()
    with tarfile.open(tar_path) as f:
        for m in f.getmembers():
            m.path = str(Path(*Path(m.path).parts[1:]))
            f.extract(m, work_path)
    copy(work_path / "LICENSE", dst_path / "LICENSE")

    tar_path.unlink()
    rmtree(work_path)


def fira_math():
    work_path = base / "fira-math-work"
    dst_path = base / "fira-math"

    if not work_path.exists():
        gh = Github()
        repo = gh.get_repo("firamath/firamath")
        Repo.clone_from(repo.clone_url, work_path)

    run(["python3", "-m", "venv", "venv"], cwd=work_path)
    run(["venv/bin/pip3", "install", "-r", "requirements.txt"], cwd=work_path)
    run(["venv/bin/python3", "scripts/build.py"], cwd=work_path)

    if dst_path.exists():
        rmtree(dst_path)
    copytree(work_path / "build", dst_path)
    copy(work_path / "LICENSE", dst_path / "LICENSE")
    rmtree(work_path)


def iosevka():
    extract_path = base / "iosevka"
    tar_path = base / "iosevka.tar.gz"
    mono_path = base / "iosevka-mono"
    quasi_path = base / "iosevka-quasi"

    if extract_path.exists():
        rmtree(extract_path)

    gh = Github()
    repo = gh.get_repo("be5invis/Iosevka")
    release = repo.get_latest_release()

    if not tar_path.exists():
        with open(tar_path, "wb") as f:
            f.write(requests.get(release.tarball_url).content)

    extract_path.mkdir()
    with tarfile.open(tar_path) as f:
        for m in f.getmembers():
            m.path = str(Path(*Path(m.path).parts[1:]))
            f.extract(m, extract_path)

    copy(base / "iosevka.toml", extract_path / "private-build-plans.toml")
    run(["npm", "install"], cwd=extract_path)
    run(
        ["npm", "run", "build", "--", "ttf::IosevkaMono", "ttf::IosevkaQuasi"],
        cwd=extract_path,
    )
    for p in (mono_path, quasi_path):
        if p.exists():
            rmtree(p)
    copytree(extract_path / "dist" / "IosevkaMono" / "TTF", mono_path)
    copytree(extract_path / "dist" / "IosevkaQuasi" / "TTF", quasi_path)
    for folder in (mono_path, quasi_path):
        copy(extract_path / "LICENSE.md", folder / "LICENSE.md")
        for p in folder.iterdir():
            if p.stem.endswith("Oblique"):
                p.unlink()

    tar_path.unlink()
    rmtree(extract_path)


def twemoji():
    work_path = base / "twemoji-work"
    dst_path = base / "twemoji-mozilla"

    if not work_path.exists():
        gh = Github()
        repo = gh.get_repo("win98se/twemoji-colr")
        repo = Repo.clone_from(repo.clone_url, work_path)
    else:
        repo = Repo(work_path)
    repo.git.checkout("patch-15")
    for p in (
        work_path / "overrides" / "1f979.svg",
        work_path / "overrides" / "1f97a.svg",
    ):
        if p.exists():
            p.unlink()
    run(["npm", "install"], cwd=work_path)
    run(["make"], cwd=work_path)

    copy(work_path / "build" / "Twemoji Mozilla.ttf", dst_path / "TwemojiMozilla.ttf")
    copy(work_path / "LICENSE.md", dst_path / "LICENSE.md")

    rmtree(work_path)


ops = {
    "cascadia": cascadia,
    "fira-math": fira_math,
    "iosevka": iosevka,
    "twemoji": twemoji,
}
parser = ArgumentParser()
parser.add_argument("modes", nargs="*")

args = parser.parse_args()
modes: list[str] = args.modes
if len(modes) == 0:
    modes = list(ops.keys())

for m in modes:
    ops[m]()
