# Yorokobi Agent

Yorokobi provides automatic database backups for web applications.

The agent is a system service that performs backups, encrypt and
transfer them to Yorokobi backup servers.

## Installation

Download the OS package from the official website, and install it using one of
the following commands.

### Ubuntu/Debian

    sudo dpkg -i yorokobi.deb

### Fedora

    sudo yum install yorokobi.rpm

## Configuration

Configuration is typically done by typing `yorokobi` which will ask for the
**license key**. After that, you're given the ability
to configure the PostgreSQL databases to work with.

Additionally, you can also configure the agent manually by editing its
configuration file located in `/etc/yorkobi.conf`.
