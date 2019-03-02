Yorokobi Agent
==============

[![Circle CI](https://img.shields.io/circleci/project/github/yorokobicom/agent/master.svg)](https://circleci.com/gh/yorokobicom/agent/tree/master)
[![ISC License](https://img.shields.io/github/license/yorokobicom/agent.svg)](https://github.com/heroku/cli/blob/master/LICENSE)

Yorokobi provides automatic database backups for web applications.

The agent is a system service that performs backups, encrypt and
transfer them to Yorokobi backup servers.

## Install

In Ubuntu 16+ simply run the following from your terminal.


    sudo snap install yorokobi --edge
    snap connect yorokobi:mount-observe
    snap connect yorokobi:process-control


For other Linux distributions [see instructions](https://docs.snapcraft.io/installing-snapd/6735).

## Getting Started

You need a [Yorokobi](https://www.yorokobi.com) account. 

To begin simply run `yorokobi setup` and follow the steps on screen.

Learn more about the [Yorokobi Agent](https://www.yorokobi.com/docs/agent).
