# Yorokobi Agent

Yorokobi provides automatic database backups for web applications.

The agent is a system service that performs backups, encrypt and
transfer them to Yorokobi backup servers.

## Installing and configuring

Foobar.

```
sudo apt-get install python3-virtualenv
python3 -m virtualenv python-env
source python-env/bin/activate
python setup.py install
```

Foobar.

# Running an agent manually

When installed with the underlying package manager, the agent typically 
is started and restarted using the following commands.

    systemctl start|stop|restart yorokobi-agent
    
However, for debugging and testing purpose, one can run an agent with 
the `yorokobid` command.

    yorokobid --conf yorokobi.conf --log yorokobi.log
    
Note that the `--conf` and `--log` flag are optional. By default it will 
create or use the configuration and log file in the current working 
directory.

# Running the simulated backup-server

In development stage, you can run a fake backup server to test the 
agent.

    python tools/backup_server.py

The backup server essentially register license key, and accept or 
refuse requested backups. It will store the accepeted backups in the 
current working directory.

    <agent-id>/
         <backup-id>/*.tar.gz
         
Foobar.
