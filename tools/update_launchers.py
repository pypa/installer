import asyncio
import pathlib
import sys

import httpx

DOWNLOAD_URL = "https://bitbucket.org/vinay.sajip/simple_launcher/downloads/{}"
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


async def _download(client: httpx.AsyncClient, name: str) -> None:
    url = DOWNLOAD_URL.format(name)
    print(f"  Fetching {url}")
    resp = await client.get(url)
    data = await resp.aread()
    VENDOR_DIR.joinpath(name).write_bytes(data)


async def main() -> None:
    print(f"Downloading into {VENDOR_DIR} ...")
    async with httpx.AsyncClient() as client:
        await asyncio.gather(*(_download(client, name) for name in LAUNCHERS))


def _patch_windows() -> None:
    # https://github.com/encode/httpx/issues/914
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


if __name__ == "__main__":
    _patch_windows()
    asyncio.run(main())
