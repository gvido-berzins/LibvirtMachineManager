# libvirt machine manager

A small virtual machine manager, mostly to test out what it possible and to create temporary virtual machines for any
disk image.

## Setup

- Minimum: Python 3.10

```bash
sudo apt install qemu # (optional) For image converter
python -m venv venv
pip install -r requirements.txt
python main.py # Check the main file main function
```

## Componenets

Manager - main.py \ 
Converter - VMDK -> QCOW2 \
Downloader - SMB image download \


The manager is the only of concern, but the other two modules can also be used when scripting
together a complete solution.

I needed qcow2 for creating snapshots and reverting, vmdk can't do that using libvirt.

For downloader, I hosted the image on an SMB share.

## Disclaimer

You can use the code however you like. The code is not a complete solution, but as an example.