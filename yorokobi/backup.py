from pathlib import PosixPath
from datetime import datetime
from threading import Thread
from tempfile import TemporaryDirectory
import subprocess
import tarfile
import pexpect
import psycopg2
from remofile import Client
from yorokobi.database import get_databases

def compute_tarball_name():
    current_time = datetime.now()
    tarball_name = current_time.strftime('%Y.%m.%d.%H.%m.%S') + '.tar.gz'

    return tarball_name

def compute_dumpall_command(username, password, hostname, port):
    host_arg = '--host=' + hostname
    port_arg = '--port=' + str(port)
    username_arg = '--username=' + username

    password_args = ''
    if password:
        password_arg = '--password'

    command = 'pg_dumpall {0} {1} {2} {3}'.format(host_arg, port_arg, username_arg, password_arg)

    print(command)
    return command

def compute_dump_command(database, username, password, hostname, port):
    host_arg = '--host=' + hostname
    port_arg = '--port=' + str(port)
    username_arg = '--username=' + username

    password_args = ''
    if password:
        password_arg = '--password'

    command = 'pg_dump -Fc {0} {1} {2} {3} {4}'.format(host_arg, port_arg, username_arg, password_arg, database)

    print(command)
    return command

def dump_database(command, database_filename, postgresql_password):
    with database_filename.open('wb') as database_file:
      child = pexpect.spawn(command, timeout=None)

      if postgresql_password:
        child.expect('Password')
        child.sendline(postgresql_password)

      database_file.write(child.read())

class Backup(Thread):
    """ Perform a backup in an external thread.

    run()
    cancel_and_wait()

    """

    def __init__(self, backup_id, port, token, config, logger):
        Thread.__init__(self)

        self.backup_id = backup_id

        self.config = config
        self.logger = logger

        self.remofile_port  = port
        self.remofile_token = token

    def run(self):
        self.logger.info("Starting backup now")
        self.logger.info("Remofile port: {0}".format(self.remofile_port))
        self.logger.info("Remofile token: {0}".format(self.remofile_token))

        temporary_dir = TemporaryDirectory()

        self.dump_databases(temporary_dir)
        self.create_tarball(temporary_dir)
        self.send_tarball(temporary_dir)

        temporary_dir.cleanup()

        self.logger.info("Backup successfully finished")

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

        self.logger.info(str(selected_dbs))

        # connect to the database and dump the selected databases
        if selected_dbs == 'all':
            try:
                connection = psycopg2.connect(dbname='postgres', user=postgresql_user, password=postgresql_password, host=postgresql_host, port=str(postgresql_port))
            except:
                print("Unable to connect to the PostgreSQL server for some reasons.")
                exit(1)

            databases = get_databases(connection)
        else:
            databases = selected_dbs

        for database in databases:
            database_filename = databases_directory / (database + '.sql')
            command = compute_dump_command(database, postgresql_user, postgresql_password, postgresql_host, postgresql_port)
            dump_database(command, database_filename, postgresql_password)

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
        self.logger.info("Sending the tarball")

        tarball_name = compute_tarball_name()

        temporary_dir = PosixPath(temporary_dir.name)
        tarbal_filename = temporary_dir / tarball_name

        self.logger.info("Sending '{0}' to {1} using Remofile protocol with port {2} and token '{3}'...".format(
            tarbal_filename, "backup.yorokobi.com", self.remofile_port, self.remofile_token))

        client = Client('backup.yorokobi.com', self.remofile_port, self.remofile_token)
        client.upload_file(tarbal_filename, '/')
