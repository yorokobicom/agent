# Yorkobi Agent Manual

This manual explains how to use the **Yorokobi Agent** to a user, from the
installation to configuration and triggering a back-up.

**Table of Contents**

- Agent installation
- Agent configuration
- Triggering a back-up
- Configuration and log file
- Alternative installation

The agent is a system service that performs backups, encrypt and transfer them
to Yorokobi backup servers.

## Agent installation

The common installation of the agent is through the underlying OS package
manager, after downloading the corresponding package file (.deb or .rpm).
However, if you're toying with the source code, you want to read the last
section "Alternative installation".

After downloading the agent package, install it using one of these two commands.

```
sudo dpkg -i yorokobi-agent.deb # for Debian/Ubuntu
sudo yum install yorokobi-agent.rpm # on Fedora
```

The package installs a service file that allows to start and stop the agent as
a system service. You can type the following commands to start, stop and
restart the agent.

```
sudo systemctl start|stop|restart yorokobi-agent
```

Note that you can also type `systemctl status yorokobi-agent` to check the
process status, but it should always be running.

If you want the agent to start at boot time, which is highly recommended, you
have to type the following.

```
sudo systemctl enable yorokobi-agent
```

After the agent is installed and running, move to the next section to configure
it to work with your **license key** and your **databases**.

## Agent configuration

The package comes with a command-line utility to communicate with the agent.
It allows you to configure the agent, check the agent status and request an
immediate back-up.

Type `yorokobi` to start configuring the agent. This command will put you in an
interactive mode to **register the agent** and **enter the database
credentials**.

Registering the agent consists of entering a **license key** and your **account
password**. After that step is completed, an **agent ID** is returned and can
be seen in your dashboard.

Entering the database credentials consists of providing the PostgreSQL database
location, the **host** (or IP) which usually is *localhost* and a **port** which
is by default 5234. There's also a **username** and a **password** to provide.
If the connection to your database was successful, you are given the ability to
select the database you wish to back-up. In most case, you just want to backup
all of them, and you'd select "All database" for that.

After you accept to save the settings, the agent is reloaded with the new
configuration values and is ready to do a backup. In fact, retyping `yorokobi`
will display the agent status this time, unless the configuration is still
incomplete. To force re-registering the agent, or changing the database
credentials, pass the `--change-license` and/or `--reconfigure-dbs` flag.

For more information, type `yorokobi --help`.

## Triggering a back-up

Additionally, there is a command to trigger a manual back-up. It comes in handy
after configuring the agent, if you want to check if the agent is working
correctly.

Type `yorokobi-backup` which will request the agent to start backing up
immediately. If it can't do it for a some reasons (either because the
configuration is not completed or the agent is already in the middle of a
back-up), it will display a message.

If the back-up was accepted, it shows a message and you can check your dashboard
to see the activity.

## Configuration and log file

It may be useful to know where the configuration and log file are located. The
configuration file resides in `/etc/yorkobi.conf` and can be manually edited.
Restart the agent to pick the new configuration values. If anything goes wrong,
checking the log file will be helpful, it's located in `/var/log/yorokobi.log`.

## Alternative installation

When the agent is not installed system-wide with the official packages, there
is no service file and therefore you need to understand how to start the agent.
Additionally, you must also be aware of configuration file, PID file and socket
file.

A typical local installation from the source code will be done in a Python
virtual environment.

```
python -m virtualenv python-env
source python-env/bin/activate
```

Inside the source code repository freshly clone, you type the following to
install the Yorokobi Agent in the Python virtual environment.

```
python setup.py install
```

On top of the usual `yorokobi` and `yorokobi-backup` binaries, there also is
`yorokodid` which the agent daemon binary. Type the following to start the
agent.

```
yorokobid
```

It's a blocking command that won't return until the agent is stopped (use a
another terminal to interact with the agent just like before). By default, it
will create `yorokobi.conf` configuration file and `yorokobi.log` lo file in
the current working directory. If there's an existing configuration file, it
will use it. You can change their location with the `--conf` and `--log` flag.
It will also creates a PID file `yorokobi.pid` which is used to shut down the
agent, and a socket file `yorokobi.sock` to do IPC (inter-process
communication). In practice, you don't need to care about the last two files.
To stop the agent, simply issue a CTRL+C signal from the first terminal.

For more information, type `yorokobid --help`.
