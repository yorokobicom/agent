# Yorokobi Agent

Yorokobi provides automatic database backups for web applications.

The agent is a system service that performs backups, encrypt and
transfer them to Yorokobi backup servers.

## Installation

Download the OS package from the official website, and install it using one of
the following commands.

```
sudo dpkg -i yorokobi-agent.deb # for Debian/Ubuntu
sudo yum install yorokobi-agent.rpm # on Fedora
```

Start the agent and make it start at boot time with the following commands.

```
sudo systemctl start yorokobi-agent
sudo systemctl enable yorokobi-agent
```

You must configure the agent.

# Configuration

Configuration is typically done by typing `yorkobi` which will ask for the
**license key** and **account password**. After that, you're given the ability
to configure the PostgreSQL databases to work with.

Additionally, you can also configure the agent manually by editing its
configuration file located in `/etc/yorkobi.conf`.
