import argparse
import subprocess
import threading
import time

import cloud_run
from cloud_run import cli
from cloud_run import images


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    parser.add_argument("--disk", default="2G")
    args = parser.parse_args()

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

        return subprocess.run(ssh_command + list(command), check=check)

    while ssh("uptime", check=False).returncode != 0:
        print("Waiting for boot")
        time.sleep(1)
    print("Booted")

    print("Shutting down...")
    ssh("sudo", "shutdown", "-h", "now", check=False)
    vm_thread.join()
    print("Finished")

