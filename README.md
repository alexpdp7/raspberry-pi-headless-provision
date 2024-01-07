# Introduction

This document provides a procedure to provision a Raspberry Pi completely headless.

* [cloud-run](https://github.com/alexpdp7/cloud-run) is a qemu wrapper that can download cloud images and spin virtual machines, and create a user with your public key
* Wireless networking is set up and seeded from existing NetworkManager wireless connections.
* After setting up a virtual machine, you burn the image to USB storage, which boots using a microSD card with UEFI firmware.

After this, you can boot the Raspberry Pi.
The Raspberry Pi connects to the wireless network and you can ssh in.

## TODO

* Create scripts to automate the process
* Set up a systemd unit that creates an SSH tunnel by connecting to a public system on the Internet.
  With this, the system is reachable even in foreign networks without port forwarding, VPNs, etc.

# Procedure

While this works, I recommend you carry out the procedure at least once with a display and keyboard to diagnose and troubleshoot.

## Prepare the UEFI microSD

To allow booting standard aarch64 images, follow the instructions from [Pi Firmware Task Force](https://github.com/pftf).
They provide UEFI firmware that you can burn to a microSD card.
The Raspberry boots from the microSD card, and the firmware then can boot from USB storage.
With this, you can use standard Linux images instead of Raspberry Pi-specific images.

* [Raspberry Pi 3](https://github.com/pftf/RPi3)

## Starting the virtual image

The following command starts an emulated virtual machine from the Debian 12 (Bullseye) generic cloud image.
The generic image includes cloud-init and hardware drivers.
(The genericcloud image includes only hardware drivers needed in virtualized environments.)

This command requires:

* `qemu-system-aarch64` (package `qemu-system-aarch64` in Arch Linux)
* `/usr/share/edk2/aarch64/QEMU_EFI.fd` (package `edk2-aarch64` in Arch Linux)

```
$ cloud-run run --create-with-base-image https://cloud.debian.org/images/cloud/bullseye/latest/debian-12-generic-arm64.qcow2 --qemu-executable qemu-system-aarch64 --machine virt --cpu cortex-a53 --no-accel --extra-qemu-opts "-bios /usr/share/edk2/aarch64/QEMU_EFI.fd" debian-bullseye-arm64
```

The terminal follows the virtual machine console.
The process ends if you shut down the virtual machine or kill the qemu process.

On my system, it takes about three minutes and a half for sshd to be ready.

## Installing wireless and network-manager

Debian cloud images do not contain the necessary firmware for wireless.
These commands also install network-manager for simpler wireless network configuration.

```
$ ssh $(cloud-run ssh debian-bullseye-arm64)
$ sudo sed -i "s/^Components: main$/Components: main non-free non-free-firmware contrib/" /etc/apt/sources.list.d/debian.sources
$ sudo apt update
$ sudo apt install firmware-brcm80211 firmware-misc-nonfree bluez-firmware raspi-firmware network-manager
```

Installing the packages (including regenerating the initrd) takes about thirteen minutes.

## Configuring wireless networks

```
$ sudo cat /etc/NetworkManager/system-connections/wifi.nmconnection | ssh $(cloud-run ssh debian-bullseye-arm64) tee wifi.nmconnection
$ ssh $(cloud-run ssh debian-bullseye-arm64)
$ sudo mv *.nmconnection /etc/NetworkManager/system-connections/
$ sudo chown root:root /etc/NetworkManager/system-connections/*.nmconnection
$ sudo chmod 600 /etc/NetworkManager/system-connections/*.nmconnection
```

## (Optional) set up a password for your user

You need this if you want to log in via the physical console.

```
$ ssh $(cloud-run ssh debian-bullseye-arm64)
$ sudo passwd $(whoami)
```

## Converting and burning the image

Shut down the VM.

Plug the USB storage.
Use `lsblk`, before and after plugging the storage, to learn the device files.
The following commands assume the USB storage is `/dev/sdb`.

You might need to unmount filesystems to prevent issues, for example.

```
$ sudo umount /dev/sdb1
```

The following commands convert the qcow2 image to raw and write the image to the USB storage.

```
$ qemu-img convert ~/.local/share/cloud_run/debian-bullseye-arm64.qcow2 image.raw
$ sudo dd if=image.raw of=/dev/sdb bs=1M status=progress
$ sudo eject /dev/sdb
$ sync; sync; sync
```

## Booting

Unplug the USB storage from your workstation.
Plug the storage to the Raspberry Pi.
Power it on.

You might need to connect a display and keyboard to see issues.

You should be able to ssh in, if you have a means to obtain the address of the system.
With proper DHCP/DNS, the host name of the system is `debian-bullseye-arm64`.

The system requires less than five minutes to boot, connect to the wireless network, and make ssh available.
