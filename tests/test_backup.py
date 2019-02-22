import time
from pathlib import PurePosixPath, PosixPath
import signal
from multiprocessing import Process
import subprocess
from tempfile import TemporaryDirectory
import logging
from remofile import Server, generate_token
from yorokobi.configuration import get_default_configuration
from yorokobi.backup import Backup
import pytest

def test_backup(postgresql, remofile):
    """ Test the backup class. """

    # todos:
    # - test a backup with selected-dbs set at 'all'
    # - test a backup with selected-dbs set at one database
    # - test interupting a backup

    root_directory, port, token = remofile

    # create a configuration that matches the fixtures
    config = get_default_configuration()
    config['postgresql-user']     = POSTGRESQL_USER
    config['postgresql-password'] = POSTGRESQL_PASSWORD
    config['postgresql-host']     = 'localhost'
    config['postgresql-port']     = POSTGRESQL_PORT
    config['selected-dbs']        = 'all'

    # create a dummy logger
    logger = logging.getLogger()

    # create the backup instance (a thread) and  starts it
    backup = Backup(BACKUP_ID, REMOFILE_PORT, REMOFILE_TOKEN, config, logger)
    backup.start()

    # wait until the backup is completed
    backup.join()

    # check the tarball created in the root directory
    root_directory = PosixPath(root_directory.name)

    files = list(root_directory.iterdir())

    assert len(files) == 1 # there's only one file in the root directory
    tarball_filename = files[0]

    # the extension of the tarball is '.tar'
    assert tarball_filename.name[:-4] == '.tar'

    # the tarball size is greater than 0
    assert tarball_filename.stat().st_size > 0

    # extract content from the tarball
    temporary_directory = TemporaryDirectory()
    tar.extract(tarball_filename, temoprary_directory.name)
