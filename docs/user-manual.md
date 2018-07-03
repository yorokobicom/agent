# The User Manual

This document explains how to use the Yorokobi agent to a user.

Table of Contents

- Getting started
- Starting the agent
- Configuring the agent
- Triggering a backup

### Getting started

Setting up the Yorokobi agent happens in three steps.

- download and install the agent
- starting the agent
- configure the agent

### Starting the agent

The Yorokobi agent is an independant process that performs back-ups 
in the background.

When the agent is installed system-wide with the underlying OS package 
manager, it's automatically started at boot time. However, it's 

```
sudo systemctl start|stop yorokobi
```

The configuration file is installed in standard system paths `/path/to/conf.file`
Additionally, a log file is present there `/path/to/log.file`.

The only expected scenario is a single instance of the agent installed 
system-wide (and thus with root priviledges). However, an instance of 
the agent can be launched with the `yorokobid` binary.

```
yorokobid --conf yorokobi.conf --log yorokobi.log
```

The two flags `--conf` and `--log` allows to adjust the location and the 
name of the configuration and log file. By default, it creates them in 
the current working directory. Run `yorokobid --help` for more information.


## Configuration the agent

After the agent is installed and running, it needs to be configured to 
work with a `backup server` and backup the relevant databases. The 
agent must be identified by the server with the license key. After that, 
credentials to database must be given.


Configuration is done with the `yorokobi` binary.

For more information, run `yorokobi --help`.

## Checking the agent status

Foobar.

## Triggering a backup

Backups are scheduled and performed transparently. However, you can 
force a backup with the `yorokobi-backupnow` binary. 

## Further settings/manipulation


--reset-flags
--reconfig-dbs
--reset-license

