# Copyright (C) Yorokobi, Inc. - All Rights Reserved
# Yorokobi Agent - Automatic database backups for web applications
#
# The source code is proprietary and confidential. Unauthorized copying
# of this file, via any medium, is strictly prohibited.
#
# Written by Jonathan De Wachter <dewachter.jonathan@gmail.com>, May 2018

import os
from pathlib import PosixPath
from configparser import ConfigParser

# A configuration file will look like the following.
#
#     [general]
#     license_key = M8ddTKx_87Iw2_EPvR9FD8Ol8_MGrqEe0LaGorsAh9Q
#     account-password = Nympij-hojbeg-cyxgi5
#     agent-id = CCMgmS99JTV7s98kc
#
#     postgresql-user = sonkun
#     postgresql-password = abcd1234
#     postgresql-host = localhost
#     postgresql-port = 5432
#
#     selected-dbs = seafile,website
#
# This will be found in a file named 'yorokobi.conf'.

def get_default_filename():
    return PosixPath(os.getcwd(), 'yorokobi.conf')

def get_default_configuration():
    """ Return the default configuration.

    The default configuration is the initial configuration before it's
    configure to work with an agent and a database. It contains the
    default values for each entry.
    """

    config = {}

    config['license-key'] = None
    config['account-password'] = None
    config['agent-id']    = None

    config['postgresql-user']     = 'postgres'
    config['postgresql-password'] = None
    config['postgresql-host']     = 'localhost'
    config['postgresql-port']     = 5432

    config['selected-dbs'] = None

    return config

def load_configuration(config_file):
    """ Read the configuration from a file.

    The configuration file is expected to be valid. This function
    doesn't perform any check and will raise an exception if it fails
    to read the file.
    """

    configparser = ConfigParser(allow_no_value=True)
    configparser.read_file(config_file)

    config = {}

    if configparser['agent']['license-key'] == 'unset':
        config['license-key'] = None
    else:
        config['license-key'] = configparser['agent']['license-key']

    if configparser['agent']['account-password'] == 'unset':
        config['account-password'] = None
    else:
        config['account-password'] = configparser['agent']['account-password']

    if configparser['agent']['agent-id'] == 'unset':
        config['agent-id'] = None
    else:
        config['agent-id'] = configparser['agent']['agent-id']

    config['postgresql-user']     = configparser['agent']['postgresql-user']
    config['postgresql-password'] = configparser['agent']['postgresql-password']
    config['postgresql-host']     = configparser['agent']['postgresql-host']
    config['postgresql-port']     = int(configparser['agent']['postgresql-port'])

    selected_dbs = configparser['agent']['selected-dbs']

    if selected_dbs == 'none':
        config['selected-dbs'] = None
    elif selected_dbs == 'all':
        config['selected-dbs'] = 'all'
    else:
        selected_dbs = selected_dbs.split(',')
        config['selected-dbs'] = selected_dbs

    return config

def save_configuration(config_file, config):
    """ Write the configuration to a file.

    The configuration file is expected to be valid. This function
    doesn't  perform any check and will raise an exception if it fails
    to write the file.
    """

    configparser = ConfigParser(allow_no_value=True)
    configparser['agent'] = {}

    if not config['license-key']:
        configparser['agent']['license-key'] = 'unset'
    else:
        configparser['agent']['license-key'] = str(config['license-key'])

    if not config['agent-id']:
        configparser['agent']['account-password'] = 'unset'
    else:
        configparser['agent']['account-password'] = str(config['account-password'])

    if not config['agent-id']:
        configparser['agent']['agent-id'] = 'unset'
    else:
        configparser['agent']['agent-id'] = str(config['agent-id'])

    configparser['agent']['postgresql-user']     = config['postgresql-user']
    configparser['agent']['postgresql-password'] = config['postgresql-password']
    configparser['agent']['postgresql-host']     = config['postgresql-host']
    configparser['agent']['postgresql-port']     = str(config['postgresql-port'])

    if config['selected-dbs'] == None:
        configparser['agent']['selected-dbs'] = 'none'
    elif config['selected-dbs'] == 'all':
        configparser['agent']['selected-dbs'] = 'all'
    else:
        configparser['agent']['selected-dbs'] = ','.join(config['selected-dbs'])

    configparser.write(config_file)
