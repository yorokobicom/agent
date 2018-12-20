# Copyright (C) LIVE INTERACTIVE SA - All Rights Reserved
# Yorokobi Agent - Automatic database backups for web applications
#
# The source code is proprietary and confidential. Unauthorized copying
# of this file, via any medium, is strictly prohibited.
#
# Written by Jonathan De Wachter <dewachter.jonathan@gmail.com>, May 2018

from pathlib import PosixPath
from datetime import datetime
from threading import Thread
from tempfile import TemporaryDirectory
from remofile import Client

import subprocess
import tarfile

def compute_tarball_name():
    current_time = datetime.now()
    tarball_name = current_time.strftime('%Y.%m.%d.%H.%m.%S') + '.tar.gz'

    return tarball_name

def compute_dump_database_command(foo, bar):
    command = 'pg_dump'

    command_args = []
    # # command_args.append('--host={0}'.format(host))
    # # command_args.append('--port={0}'.format(port))
    # command_args.append('--username={0}'.format(name))
    #
    # # if password:
    #     # command_args.append('--password={0}'.format(password))
    # # else:
    #     # command_args.append('--no-password')
    #
    # command_args.append('--dbname={0}'.format(db))

    return [command, *commands]

class Backup(Thread):
    """ Perform a backup in an external thread.

    run()
    cancel_and_wait()

    """

    def __init__(self, port, token, config):
        Thread.__init__(self)

        self.config = config

        self.remofile_port  = port
        self.remofile_token = token

    def run(self):
        temporary_dir = TemporaryDirectory()

        self.dump_databases(temporary_dir)
        self.create_tarball(temporary_dir)
        self.send_tarball(temporary_dir)

        temporary_dir.cleanup()

    def cancel_and_wait(self):
        pass # to be implemented

    def dump_databases(self, temporary_dir):
        # /tmp/abcd/2018.05.04.14.00.03.tar.gz
        #           backups/databases/PostgreSQL/<db-name>.sql

        # create destination directories /backups/databases/PostgreSQL

        # retrieve needed information to connect to the database and
        # dump their content
        postgresql_user     = self.config['postgresql-user']
        postgresql_password = self.config['postgresql-password']
        postgresql_host     = self.config['postgresql-host']
        postgresql_port     = self.config['postgresql-port']

        selected_dbs = self.config['selected-dbs']


        # compute dirs
        temporary_dir = PosixPath(temporary_dir.name)
        assert temporary_dir.exists() and temporary_dir.is_dir()

        databases_directory = temporary_dir / 'backups' / 'databases' / 'PostgreSQL'
        databases_directory.mkdir(parents=True, exist_ok=False)

        #
        # # connect to the database and dump the selected databases
        # for database in selected_dbs:
        #     database_filename = databases_directory / (database + '.sql')
        #     print(database_filename)
        #
        #     database_file = database_filename.open('w')
        #
        #     command = compute_dump_database_command(foo, bar)
        #     subprocess.run(command, stdout=database_file)
        #     database_file.close()
        #
        #     database_file = database_filename.open('r')
        #     print(database_file.read())

    def create_tarball(self, temporary_dir):
        # compute tarball name (something like this '2018.05.04.14.00.03.tar.gz')
        tarball_name = compute_tarball_name()

        temporary_dir = PosixPath(temporary_dir.name)
        tarbal_filename = temporary_dir / tarball_name
        tarball_source  = temporary_dir / 'backups'

        tarball = tarfile.open(tarbal_filename, "w")
        tarball.add(tarball_source, arcname="backups")
        tarball.close()

    def send_tarball(self, temporary_dir):
        tarball_name = compute_tarball_name()

        temporary_dir = PosixPath(temporary_dir.name)
        tarbal_filename = temporary_dir / tarball_name

        client = Client('18.191.159.255', self.remofile_port, self.remofile_token)
        client.upload_file(tarbal_filename, '/')
