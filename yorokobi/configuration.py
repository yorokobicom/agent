# Copyright (C) LIVE INTERACTIVE SA - All Rights Reserved
# Yorokobi Agent - Automatic database backups for web applications
#
# The source code is proprietary and confidential. Unauthorized copying
# of this file, via any medium, is strictly prohibited.
#
# Written by Jonathan De Wachter <dewachter.jonathan@gmail.com>, May 2018

"""
[general]
backup-hostname = backup.yorokobi.co
backup-port = 12345

license_key = FOOBAr
agent-id = foobar

postgresql_host = sonkun
postgresql_password = ''
postgresql_host = localhost
postgresql_port = 5123

selected_databases = []
"""

import os 
from pathlib import PosixPath
from configparser import ConfigParser

# BACKUP_HOSTNAME = 'backup.yorokobi.co'
BACKUP_HOSTNAME = '127.0.0.1' # FIX-ME
BACKUP_PORT = 6769

def get_default_filename():
    return PosixPath(os.getcwd(), 'yorokobi.conf')
    
def get_default_configuration():
    config = {}
    
    # config['backup-host'] = 'backup.yorokobi.co'
    # config['backup-port'] = 12345

    # config['license-key'] = 'SKSICNALASCMASKCKASMCJDFVJFJFJV'
    # config['agent-id']    = 1122334455
    config['license-key'] = None
    config['agent-id']    = None

    config['postgresql-user']     = 'postgres'
    config['postgresql-password'] = None
    config['postgresql-host']     = 'localhost'
    config['postgresql-port']     = 5432

    config['selected-dbs'] = None
    
    return config
    
def load_configuration(config_file):
    """ Read the configuration from a file.
    
    This function may raise an exception.
    
    Long description.
    """
    
    configparser = ConfigParser(allow_no_value=True)
    configparser.read_file(config_file)
    
    config = {}
    
    config['license-key'] = configparser['agent']['license-key']
    config['agent-id']    = int(configparser['agent']['agent-id'])
    
    config['postgresql-user']     = configparser['agent']['postgresql-user']
    config['postgresql-password'] = configparser['agent']['postgresql-password']
    config['postgresql-host']     = configparser['agent']['postgresql-host']
    config['postgresql-port']     = int(configparser['agent']['postgresql-port'])
    
    return config
    
def save_configuration(config_file, config):
    configparser = ConfigParser(allow_no_value=True)
    configparser['agent'] = {}
    
    configparser['agent']['license-key'] = config['license-key']
    configparser['agent']['agent-id']    = str(config['agent-id'])
    
    configparser['agent']['postgresql-user']     = config['postgresql-user']
    configparser['agent']['postgresql-password'] = config['postgresql-password']
    configparser['agent']['postgresql-host']     = config['postgresql-host']
    configparser['agent']['postgresql-port']     = str(config['postgresql-port'])
    
    configparser.write(config_file)
