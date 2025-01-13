from __future__ import annotations

import asyncio
import io
import pathlib
import sys
import tarfile
from typing import Any

import httpx

DISTLIB_URL = "https://pypi.org/simple/distlib"
VENDOR_DIR = (
    pathlib.Path(__file__)
    .parent.parent.joinpath("src", "installer", "_scripts")
    .resolve()
)

LAUNCHERS = [
    "t32.exe",
    "t64.exe",
    "t_arm.exe",
    "t64-arm.exe",
    "w32.exe",
    "w64.exe",
    "w_arm.exe",
    "w64-arm.exe",
]


async def _get_distlib_page(client: httpx.AsyncClient) -> Any:
    resp = await client.get(
        DISTLIB_URL,
        headers={"ACCEPT": "application/vnd.pypi.simple.v1+json"},
        follow_redirects=True,
    )
    return resp.json()


def _get_link_from_response(json_response: dict[str, Any]) -> tuple[str, str] | None:
    version = max(version_str.split(".") for version_str in json_response["versions"])
    filename = f"distlib-{'.'.join(version)}.tar.gz"
    for file_info in json_response["files"]:
        if file_info["filename"] == filename:
            return file_info["url"], filename
    return None


async def _download_distlib(client: httpx.AsyncClient) -> bytes | None:
    distlib_page = await _get_distlib_page(client)
    data = None
    if pair := _get_link_from_response(distlib_page):
        url, filename = pair
        print(f"  Fetching {filename}")
        resp = await client.get(url)
        data = await resp.aread()
    return data


def _get_launcher_path(names: list[str], launcher: str) -> str | None:
    if paths := [name for name in names if launcher in name]:
        return paths[0]
    return None


def _unpack_launchers_to_dir(distlib_tar: bytes) -> None:
    print("Unpacking launchers")
    with tarfile.open(fileobj=io.BytesIO(distlib_tar)) as file:
        for launcher_name in LAUNCHERS:
            if (path := _get_launcher_path(file.getnames(), launcher_name)) and (
                launcher := file.extractfile(path)
            ):
                print(f"  Unpacking {launcher_name}")
                VENDOR_DIR.joinpath(launcher_name).write_bytes(launcher.read())


async def main() -> None:
    print(f"Downloading into {VENDOR_DIR} ...")
    async with httpx.AsyncClient() as client:
        data = await _download_distlib(client)
    if data is not None:
        _unpack_launchers_to_dir(data)
    print("Scripts update failed!")


def _patch_windows() -> None:
    # https://github.com/encode/httpx/issues/914
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


if __name__ == "__main__":
    _patch_windows()
    asyncio.run(main())
