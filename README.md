# Quick start

This repo provides a command to provision a Raspberry Pi completely headless using cloud images of Linux distributions.

## Requirements

* `qemu-system-aarch64` (package `qemu-system-aarch64` in Arch Linux)
* `/usr/share/edk2/aarch64/QEMU_EFI.fd` (package `edk2-aarch64` in Arch Linux)

## Procedure

While this works, I recommend you carry out the procedure at least once with a display and keyboard to diagnose and troubleshoot.

### Prepare the UEFI microSD

To allow booting standard aarch64 images, follow the instructions from [Pi Firmware Task Force](https://github.com/pftf).
They provide UEFI firmware that you can burn to a microSD card.
The Raspberry boots from the microSD card, and the firmware then can boot from USB storage.
With this, you can use standard Linux images instead of Raspberry Pi-specific images.

* [Raspberry Pi 3](https://github.com/pftf/RPi3)

### Create and burn the image

```
$ rphp example --wifi-file wifi
```

`wifi` is a file containing ESSIDs and their passwords:

```
essid1,password
...
```

Running the command will take a good while and produce an `example.raw` disk image you can write to a USB drive:

```
$ sudo dd if=example.raw of=/dev/... bs=1M status=progress
```

After this, you can boot the Raspberry Pi.
The Raspberry Pi connects to the wireless network and you can ssh in.
(The process copies your public key.)

# Scripts

Use the `--script` option to provide scripts that run after the standard provisioning.
The scripts must be bash scripts.
They run as root.

The `provision-tvheadend` file is an example that sets up Tvheadend.

# About

## Should you do this?

Probalby not.

Raspberry Pi OS has support to do this configuration headlessly too.
Because Raspberry Pi OS images already have all the necessary packages preinstalled, alterations required to the image are simpler.

This procedure is interesting because in theory you could customize any cloud image in this way, and the resulting images are less Raspberry Pi-specific.
(You can also adapt this procedure to other hardware, even standard x86 computers.)
However, there are not many Linux distributions which provide cloud images *and* the necessary Raspberry Pi hardware support.
Additionally, those Linux distributions might provide images more suitable for Raspberries (e.g. with the right hardware support preinstalled).

So there might be better ways to achieve these objectives.
However, you might like:

* Using Debian upstream instead of the tuned Raspberry Pi OS
* Without using the *unofficial* Raspberry Pi Debian images
* Having a procedure that can be adapted to other devices, which uses less Raspberry Pi customization
* Learning about cloud images and provisioning

# TODO

* Set up a systemd unit that creates an SSH tunnel by connecting to a public system on the Internet.
  With this, the system is reachable even in foreign networks without port forwarding, VPNs, etc.
