import json
import os
import re
import shutil
import subprocess
import sys
import argparse
import urllib.request

PIP_PACKAGE = "mitmproxy"
DOCKER_REPOSITORY = "mitmproxy/mitmproxy"
GO_PACKAGE = "github.com/mccutchen/go-httpbin/v2"
GO_BINARY = f"{GO_PACKAGE}/cmd/go-httpbin"

_RE_PIP_VERSIONS_1 = re.compile(r"\(from versions: (.*)\)")


def get_pip_versions_1(package: str) -> list[str]:
    process = subprocess.run(["pip", "install", f"{package}=="], capture_output=True)
    if match := _RE_PIP_VERSIONS_1.search(process.stderr.decode()):
        return match.group(1).split(", ")


def get_pip_versions_2(package: str) -> list[str]:
    url = f"https://pypi.org/pypi/{package}/json"
    response = urllib.request.urlopen(url)
    assert 200 == response.status
    return list(json.loads(response.read())["releases"])


def get_pip_versions_3(package: str) -> list[str]:
    process = subprocess.run(
        ["pip", "index", "versions", package], capture_output=True, check=True
    )
    return process.stdout.decode().splitlines()[1][20:].split(", ")[::-1]


def get_pip_versions(package: str) -> list[str]:
    return get_pip_versions_1(package)


def get_pip_version_1(package: str) -> str:
    return get_pip_versions_1(package)[-1]


def get_pip_version_2(package: str) -> str:
    return get_pip_versions_2(package)[-1]


def get_pip_version_3(package: str) -> str:
    return get_pip_versions_3(package)[-1]


def get_pip_version_4(package: str) -> str:
    subprocess.check_call(["pip", "install", "--upgrade", package])
    process = subprocess.run(["pip", "freeze"], capture_output=True, check=True)
    for frozen in process.stdout.decode().splitlines():
        if frozen.startswith(f"{package}=="):
            return frozen[11:]
    raise ModuleNotFoundError()


def get_pip_version(package: str) -> str:
    return get_pip_version_1(package)


def get_go_versions(module: str) -> list[str]:
    process = subprocess.run(
        ["go", "list", "-json", "-m", "-versions", module],
        capture_output=True,
        check=True,
    )
    return json.loads(process.stdout)["Versions"]


def get_go_version(module: str) -> str:
    return get_go_versions(module)[-1]


def get_docker_versions(repository: str) -> list[str]:
    url = f"https://hub.docker.com/v2/repositories/{repository}/tags?page_size={sys.maxsize}"
    response = urllib.request.urlopen(url)
    assert 200 == response.status
    return [result["name"] for result in json.loads(response.read())["results"]]


def check_pip_version(package: str, repository: str) -> bool:
    return get_pip_version(package) in get_docker_versions(repository)


def check_go_version(module: str, repository: str) -> bool:
    return get_go_version(module) in get_docker_versions(repository)


def make_wheel(package: str):
    if os.path.isdir(package):
        shutil.rmtree(package)
    subprocess.check_call(["pip", "wheel", f"--wheel-dir={package}", package])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("repository")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--pip")
    group.add_argument("--go")
    args = parser.parse_args()
    if args.pip:
        check = check_pip_version(args.pip, args.repository)
    elif args.go:
        check = check_go_version(args.go, args.repository)
    else:
        raise ValueError()
    print(f"changed={str(not check).lower()}")


if __name__ == "__main__":
    main()
