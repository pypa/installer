import asyncio
import pathlib
import sys

import httpx

DOWNLOAD_URL = "https://api.bitbucket.org/2.0/repositories/vinay.sajip/simple_launcher/downloads/{}"
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
LONGEST_NAME_LENGTH = max(len(name) for name in LAUNCHERS)


async def _download(client: httpx.AsyncClient, name: str) -> None:
    url = DOWNLOAD_URL.format(name)
    print("GET", url)
    resp = await client.get(url)
    resp.raise_for_status()
    data = await resp.aread()
    VENDOR_DIR.joinpath(name).write_bytes(data)
    print("  Downloaded", name.ljust(LONGEST_NAME_LENGTH), len(data), "bytes")


async def main() -> None:
    print("Destination", VENDOR_DIR)
    async with httpx.AsyncClient(follow_redirects=True) as client:
        await asyncio.gather(*(_download(client, name) for name in LAUNCHERS))


def _patch_windows_38() -> None:
    # https://github.com/encode/httpx/issues/914
    if sys.version_info >= (3, 8) and sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


if __name__ == "__main__":
    _patch_windows_38()
    asyncio.run(main())
