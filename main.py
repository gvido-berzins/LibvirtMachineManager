from contextlib import contextmanager
from pathlib import Path
import time
from uuid import uuid4

import libvirt

from download import download
from utils import format_str_path, path_to_str


class VMManager:
    def __init__(self, connection_string: str = "qemu:///system") -> None:
        self.conn_string: str = connection_string
        self.conn: libvirt.virConnect = None
        self.username = "osboxes"
        self.password = "osboxes.org"
        self.image_path = format_str_path("64bit/Linux Lite 5.8 (64bit).vmdk")
        self.template_path = Path("temp-template.xml")
        self.snapshot_template_path = Path("temp-snapshot-template.xml")

    def __enter__(self):
        self.conn = libvirt.open(self.conn_string)
        if not self.conn:
            raise SystemExit("Failed to open connection to qemu:///system")
        return self

    def __exit__(self, *exc_info) -> None:
        self.conn.close()

    def list_domains(self):
        """Print all existing domains"""
        domains = self.conn.listAllDomains()
        print("Stats:")
        for dev in domains:
            print(dev.name())

    def domain_by_name(self, name: str):
        """Find a domain by name"""
        try:
            return self.conn.lookupByName(name)
        except libvirt.libvirtError:
            return print(f"Could not find domain: {name}")

    def rename_domain(self, name: str, new_name: str) -> None:
        """Rename an existing domain"""
        domain = self.domain_by_name(name)
        domain.rename("kali-main")

    def list_domain_snapshots(self, name: str):
        """Print all snapshots for a domain by name"""
        domain = self.domain_by_name(name)
        snapshots = domain.snapshotListNames()
        for snapshot in snapshots:
            r = domain.snapshotLookupByName(snapshot)
            print(r.getName(), r.isCurrent())

    def save_domain_snapshots(self, name: str):
        """Save all snapshots for a domain by name"""
        domain = self.domain_by_name(name)
        snapshots = domain.snapshotListNames()
        for snapshot in snapshots:
            r = domain.snapshotLookupByName(snapshot)
            xml = r.getXMLDesc()
            Path(f"{name}-{r.getName()}-snapshot.xml").write_text(xml)
            print(r.getName(), r.isCurrent())

    def list_all_volumes(self):
        """Print all existing volumes in all storage pools"""
        pools = self.conn.listAllStoragePools()
        for pool in pools:
            for vol in pool.listAllVolumes():
                print(f"{pool.name():<20}: {vol.name()}")

    def save_xml(self, name: str) -> Path:
        """Save domain XML to a file with name 'save-{name}.xml'"""
        temp = self.conn.lookupByName(name)
        desc = temp.XMLDesc()
        path = Path(f"save-{name}.xml")
        path.write_text(desc)
        return path

    def delete_domain_if_exists(self, name: str) -> None:
        """Undefine a domain if it exists, if it's running, destroy it"""
        try:
            domain = self.domain_by_name(name)

            while domain.isActive():
                domain.destroy()
                time.sleep(1)
            domain.undefine()
        except (libvirt.libvirtError, AttributeError):
            print(f"{name}: does not exist!")

    def domain_from_template(
        self, template: Path, name: str, image_path: str, define: bool = False
    ) -> libvirt.virDomain:
        """Create a new domain from a given XML template. Defined and Run."""
        self.delete_domain_if_exists(name)
        map = dict(NAME=name, IMAGE_PATH=image_path, UUID=uuid4())
        xml = template.read_text()
        for template_str, value in map.items():
            xml = xml.replace(f"${template_str}", str(value))
        if define:
            domain = self.conn.defineXML(xml)
        else:
            domain = self.conn.createXML(xml)
        return domain

    def snapshot_from_template(
        self, template: Path, domain_name: str, snapshot_name: str, image_path: str
    ) -> libvirt.virDomainSnapshot:
        """Create a new domain snapshot from an XML template"""
        map = dict(
            DOMAIN_NAME=domain_name,
            SNAPSHOT_NAME=snapshot_name,
            IMAGE_PATH=image_path,
            UUID=uuid4(),
            CREATION_TIME=int(time.time()),
        )
        xml = template.read_text()
        for template_str, value in map.items():
            xml = xml.replace(f"${template_str}", str(value))
        domain = self.domain_by_name(domain_name)
        snapshot = domain.snapshotCreateXML(xml)
        return snapshot

    @contextmanager
    def temp_domain(self, name: str = "", timeout: int = 30) -> libvirt.virDomain:
        """Temporary domain context manager to create and delete on the fly"""
        name = name if name else str(uuid4())
        print(f"{name=}")
        domain = self.domain_from_template(self.template_path, name, self.image_path)
        start_time = time.time()
        try:
            while not domain.isActive:
                if time.time() - start_time > timeout:
                    break
            yield domain
        finally:
            self.delete_domain_if_exists(name)

    @contextmanager
    def temp_domain_defined(self, name: str = "", timeout: int = 30) -> libvirt.virDomain:
        """Temporary domain context manager to define and delete on the fly"""
        name = name if name else str(uuid4())
        print(f"{name=}")
        domain = self.domain_from_template(
            self.template_path, name, self.image_path, define=True
        )
        start_time = time.time()
        try:
            while not domain.isActive:
                if time.time() - start_time > timeout:
                    break
            yield domain
        finally:
            self.delete_domain_if_exists(name)

    @contextmanager
    def temp_domain_snapshot(
        self, name: str = "", timeout: int = 30
    ) -> libvirt.virDomain:
        """Temporary domain context manager to define a domain and create a snapshot and
        revert afterwards"""
        name = name if name else str(uuid4())
        print(f"{name=}")
        domain = self.domain_from_template(
            template=self.template_path,
            name=name,
            image_path=self.image_path,
            define=True,
        )
        snapshot = self.snapshot_from_template(
            template=self.snapshot_template_path,
            domain_name=name,
            snapshot_name="main",
            image_path=self.image_path,
        )

        start_time = time.time()
        try:
            while not domain.isActive:
                if time.time() - start_time > timeout:
                    break
            yield domain
        finally:
            domain.revertToSnapshot(snapshot)
            self.delete_domain_if_exists(name)


def image_download_strategy():
    """Temporary image by downloading a new image from an smbshare and/or extracting it"""
    with VMManager() as vm:
        vm.image_path = str(download())
        with vm.temp_domain() as domain:
            print(domain.name(), domain.isActive())
            input("Press any key to shut down")
        vm.list_domains()


def standard_strategy():
    """Temporary image using an existing image and only creating it"""
    with VMManager() as vm:
        with vm.temp_domain() as domain:
            print(domain.name(), domain.isActive())
            input("Press any key to shut down")
        vm.list_domains()


def define_strategy():
    """Temporary image using an existing image and only defining it"""
    with VMManager() as vm:
        with vm.temp_domain_defined() as domain:
            print(domain.name(), domain.isActive())
            input("Press any key to shut down")
        vm.list_domains()


def image_snapshot_strategy():
    """Temporary image using on-the-fly snapshots

    (NOT IMPLEMENTED): Need to switch from vmdk to QCOW2 on download step, but it works"""
    with VMManager() as vm:
        vm.image_path = path_to_str("64bit/Linux Lite 5.8 (64bit).qcow2")
        vm.template_path = Path("temp-qcow2-template.xml")
        with vm.temp_domain_snapshot() as domain:
            print(domain.name(), domain.isActive())
            input("Press any key to shut down")
        vm.list_domains()


def main():
    standard_strategy()
    # define_strategy()
    # image_download_strategy() # TDB
    # image_snapshot_strategy()


if __name__ == "__main__":
    main()
