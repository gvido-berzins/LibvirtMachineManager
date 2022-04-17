"""
Summary:
    Convert a vmdk vmware image to qcow2 image
CLI:
    qemu-img convert image.vmdk -O qcow2 image.qcow2
"""
import sys
from pathlib import Path
import subprocess
import shlex

from utils import str_to_path


def vmdk_to_qcow(path: Path):
    outpath = path.parent
    new_path = outpath / f"{path.stem}.qcow2"
    cmd = f"qemu-img convert {path} -O qcow2 {new_path}"
    ret = subprocess.call(shlex.split(cmd))
    if ret == 1:
        print("Failed to convert file. Make sure the file exists or you have permissions")
        sys.exit(1)
    return new_path


def main():
    path = str_to_path("64bit/Linux Lite 5.8 (64bit).vmdk")
    path = vmdk_to_qcow(path)
    print(f"New Path: {path}")


if __name__ == "__main__":
    main()
