Yorokobi Agent
==============

[![Circle CI](https://img.shields.io/circleci/project/github/yorokobicom/agent/master.svg)](https://circleci.com/gh/yorokobicom/agent/tree/master)
[![Snap Status](https://build.snapcraft.io/badge/yorokobicom/agent.svg)](https://build.snapcraft.io/user/yorokobicom/agent) 
[![ISC License](https://img.shields.io/github/license/yorokobicom/agent.svg)](https://github.com/heroku/cli/blob/master/LICENSE)

Yorokobi provides automatic database backups for web applications.

The agent is a system service that performs backups, encrypt and
transfer them to Yorokobi backup servers.

## Install

In Ubuntu 16+ simply run the following from your terminal.


    snap install yorokobi


For other Linux distributions [see instructions](https://docs.snapcraft.io/installing-snapd/6735).

## Configure

You need a [Yorokobi](https://www.yorokobi.com) account. 

To configure simply run `yorokobi` and enter your Yorokobi 
**license key**.

Follow the steps to configure the PostgreSQL databases to work with.

Alternatively, you can configure the agent manually by editing its
configuration file located in `/etc/yorokobi.conf`.
