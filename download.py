from pathlib import Path
from urllib.parse import urlparse
import os
from smb.SMBConnection import SMBConnection
import py7zr

IMAGE_NAME = "linux-lite-58.7z"
SMB_SHARE = "CHANGEME"
SMB_HOST = "CHANGEME"
IMAGE_URL = f"smb://{SMB_HOST}/{SMB_SHARE}/{IMAGE_NAME}"
USERNAME = os.environ["SMB_USER"]
PASSWORD = os.environ["SMB_PASS"]
EXPECTED_FILE_SIZE = "1397456323"  # To avoid secondary download


def smb_get_file(url: str, local_path: Path):
    purl = urlparse(url)
    share, path = purl.path.split("/")[1:]
    conn = SMBConnection(USERNAME, PASSWORD, "l", "r", is_direct_tcp=True)
    assert conn.connect(purl.netloc, 445)

    if local_path.exists():
        remote_size = conn.getAttributes(share, path).file_size
        if remote_size == local_path.stat().st_size:
            return print("File already exists")

    conn.retrieveFile(share, path, local_path.open("wb"))


def extract(path: Path):
    archive = py7zr.SevenZipFile(path, mode="r")
    archive.extractall()
    archive.close()


def download() -> Path:
    download_path = Path(IMAGE_NAME)
    print("DOWNLOADING IMAGE".center(60, "-"))
    smb_get_file(IMAGE_URL, download_path)

    print("EXTRACTING".center(60, "-"))
    extract(download_path)

    return Path("64bit/Linux Lite 5.8 (64bit).vmdk").resolve()


if __name__ == "__main__":
    download()
