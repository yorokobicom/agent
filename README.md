Yorokobi Agent
==============

[![Circle CI](https://img.shields.io/circleci/project/github/yorokobicom/agent/master.svg)](https://circleci.com/gh/yorokobicom/agent/tree/master)
[![ISC License](https://img.shields.io/github/license/yorokobicom/agent.svg)](https://github.com/heroku/cli/blob/master/LICENSE)

Yorokobi provides automatic backups for databases, web applications and file systems.

The agent is a system service that performs backups and encrypts.

## Setup

Run the setup to setup databases, folders and the path where to store backups.

    ./yorokobi setup

## Usage

```
Usage:
    yorokobi <command> [options]

Commands:
    setup     Configure backup settings and initialize repository
    backup    Run a one-time backup
    start     Start the backup daemon in the background
    restore   Restore from a backup snapshot    
    help      Show this help message

For more information about a command:
    yorokobi help <command>
```