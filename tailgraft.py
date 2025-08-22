#!/usr/bin/env python3

import json
import os
import sys


flags = [
    "tailscale",
    "up",
    "--ssh",
] 
hostname = ""

def lsblk_linux():
    return json.loads(os.popen("lsblk --json").read())

def find_user_data():
    # Linux-only: scan mounted block devices for a 'user-data' file
    devices = lsblk_linux().get('blockdevices', [])
    for dev in devices:
        mountpoint = dev.get("mountpoint")
        if mountpoint and os.path.isfile(os.path.join(mountpoint, 'user-data')):
            return os.path.join(mountpoint, 'user-data')
        children = dev.get("children")
        if children:
            for child in children:
                cmount = child.get("mountpoint")
                if cmount and os.path.isfile(os.path.join(cmount, 'user-data')):
                    return os.path.join(cmount, 'user-data')
    return None

def prompt_user(prompt, allowed_replies = []):
    while True:
        reply = input(prompt)
        if allowed_replies != []:
            if reply in allowed_replies:
                return reply
            else:
                print("Invalid reply. Please try again.")
        else:
            return reply

def check_root():
    if os.geteuid() != 0:
        print("This script must be run as root. Re-executing with sudo...")
        os.execvp('sudo', ['sudo', 'python3'] + sys.argv)

def main():
    check_root()
    user_data_fname = find_user_data()
    if user_data_fname is None:
        print("Could not find user-data file. Please try removing your SD card and re-inserting it.")
        sys.exit(1)

    print("Found user-data file at {}".format(user_data_fname))

    # Removed exit node prompt and configuration

    authkey = input("Please enter your Tailscale authkey: ")
    flags.append("--authkey={}".format(authkey))

    hostname = input("Please enter a hostname for this device: ")
    if hostname != "":
        flags.append("--hostname={}".format(hostname))

    print("Adding Tailscale to user-data file...")

    with open(user_data_fname, 'a') as f:
        f.write("runcmd:\n")
        f.write("  - [ \"sh\", \"-c\", \"curl -fsSL https://tailscale.com/install.sh | sh\" ]\")
        f.write("\n")
        # Removed ip_forward and IPv6 forwarding configuration as it's exit-node related
        f.write("  - {}\n".format(json.dumps(flags)))
        if hostname != "":
            f.write("  - [ \"sh\", \"-c\", \"sudo hostnamectl hostname {}\" ]\".format(hostname))
            f.write("\n")

    print("Tailscale will be installed on boot. Please eject your SD card and boot your raspi.")
    print("Good luck!")


if __name__ == "__main__":
    main()