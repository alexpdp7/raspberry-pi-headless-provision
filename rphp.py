import argparse
import base64
import pathlib
import shlex
import subprocess
import textwrap
import threading
import time
import uuid

import cloud_run
from cloud_run import cli
from cloud_run import images


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    parser.add_argument("--disk", default="2G")
    parser.add_argument("--wifi-file", type=pathlib.Path)
    parser.add_argument("--reuse", action="store_true")
    parser.add_argument("--script", type=pathlib.Path, action="append")
    args = parser.parse_args()

    wifi_networks = []
    if args.wifi_file:
        wifi_file: pathlib.Path = args.wifi_file
        for ssid, psk in [l.split(",") for l in wifi_file.read_text().splitlines()]:
            connection_uuid = uuid.uuid4()
            configuration_file = textwrap.dedent(f"""
                [connection]
                id={ssid}
                uuid={connection_uuid}
                type=wifi
                interface-name=wlan0

                [wifi]
                mode=infrastructure
                ssid={ssid}

                [wifi-security]
                auth-alg=open
                key-mgmt=wpa-psk
                psk={psk}

                [ipv4]
                method=auto

                [ipv6]
                addr-gen-mode=stable-privacy
                method=auto

                [proxy]
            """).lstrip()
            configuration_file = base64.b64encode(configuration_file.encode("utf8")).decode("utf8")
            wifi_networks.append((ssid, configuration_file))

    if not args.reuse:
        images.rm_vm(args.name)

        vm_thread = threading.Thread(target=cloud_run.run_vm, kwargs=dict(
            create_with_base_image="https://cloud.debian.org/images/cloud/bullseye/latest/debian-11-generic-arm64.qcow2",
            instance_id=args.name,
            qemu_executable="qemu-system-aarch64",
            machine="virt",
            cpu="cortex-a53",
            accel=False,
            extra_qemu_opts="-bios /usr/share/edk2/aarch64/QEMU_EFI.fd",
            mem="1G",
            disk=args.disk,
            smp="cpus=1",
        ))

        vm_thread.start()

    def ssh(*command, check=True):
        while True:
            try:
                ssh_command = ["ssh"] + cli.ssh(args.name)
                break
            except:
                print("Waiting for state")
                time.sleep(1)

        command = ssh_command + list(command)
        print(shlex.join(command))
        return subprocess.run(command, check=check)

    while ssh("uptime", check=False).returncode != 0:
        print("Waiting for boot")
        time.sleep(1)
    print("Booted")
    # watch out for the ugly ', due to ssh's bizarre arg parsing :(
    ssh("sudo", "sed", "-i", "'s/main$/main non-free contrib/'", "/etc/apt/sources.list")
    ssh("sudo", "apt", "update")
    ssh("sudo", "apt", "install", "-y", "firmware-brcm80211", "firmware-misc-nonfree", "bluez-firmware", "network-manager")

    for ssid, configuration_file in wifi_networks:
        file = f"/etc/NetworkManager/system-connections/{ssid}.nmconnection"
        # more bad escaping :(
        ssh("sh", "-c", f"'echo {configuration_file} | base64 -d | sudo tee {file}'")
        ssh("sudo", "chmod", "600", file)

    for script in args.script:
        script = base64.b64encode(script.read_bytes()).decode("utf8")
        ssh("sh", "-c", f"'echo {script} | base64 -d | sudo bash -x'")

    if not args.reuse:
        print("Shutting down...")
        ssh("sudo", "shutdown", "-h", "now", check=False)
        vm_thread.join()
    image_file = f"{args.name}.raw"
    print(f"Finished, writing image {image_file}")
    subprocess.run(["qemu-img", "convert", images.get_vm_img_path(args.name), f"{args.name}.raw"], check=True)
    print(f"Written {image_file}")
