# Copyright (C) LIVE INTERACTIVE SA - All Rights Reserved
# Yorokobi Agent - Automatic database backups for web applications
#
# The source code is proprietary and confidential. Unauthorized copying
# of this file, via any medium, is strictly prohibited.
#
# Written by Jonathan De Wachter <dewachter.jonathan@gmail.com>, May 2018

from threading import Thread
from remofile import Client

class Backup(Thread):
    """ Perform a backup in an external thread.
    
    start()
    stop()
    
    cancel()
    is_terminated()
    get_status()
    
    """
    
    def __init__(self, backup_id, port, token):
        Thread.__init__(self)
    
        self.client = Client(port, token)
        self.is_terminated = False
        
    def __del__(self):
        pass
        
    def run(self):

        # create temporary directory
        
        # 1 - do actual backups and put in tmp dir
        # 2 - encrypt directory
        # 3 - upload tar 
        #     self.client.upload_file(tmp_directory.name, '/')
        
        self.is_terminated = True
        
        pass

# # constructed with tmp directory, database credential
# # is finnished or not
#
#     # implement backup code here and later put it in relevant places
#     # 1. create temporary directory
#     # 2. read configure file (get database credentials)
#     # 3. dumb database into .sql in the tmp dir
#     # 4. create tarball
#     # 5. encrypt tarballl
#     # 6. send it over with remofile
# 
#     from pathlib import PosixPath
#     import subprocess
#     from tempfile import TemporaryDirectory
#     from datetime import datetime
#     import tarfile
# 
#     def dump_databases(dbs, host, port, name, password=None, tmp_dir=None):
#         # /tmp/abcd/2018.05.04.14.00.03.tar.gz
#         #           backups/databases/PostgreSQL/<db-name>.sql
# 
#         # create destination directories /backups/databases/PostgreSQL
#         print(tmp_dir)
# 
#         tmp_dir = PosixPath(tmp_dir)
#         assert tmp_dir.exists() and tmp_dir.is_dir()
# 
#         print(tmp_dir)
#         databases_directory = tmp_dir / 'backups' / 'databases' / 'PostgreSQL'
#         print(databases_directory)
#         databases_directory.mkdir(parents=True, exist_ok=False)
# 
#         for db in dbs:
#             print(db)
# 
#             database_filename = databases_directory / (db + '.sql')
#             print(database_filename)
# 
#             database_file = database_filename.open('w')
# 
#             command = 'pg_dump'
# 
#             command_args = []
#             # command_args.append('--host={0}'.format(host))
#             # command_args.append('--port={0}'.format(port))
#             command_args.append('--username={0}'.format(name))
# 
#             # if password:
#                 # command_args.append('--password={0}'.format(password))
#             # else:
#                 # command_args.append('--no-password')
# 
#             command_args.append('--dbname={0}'.format(db))
# 
#             print([command, *command_args])
#             subprocess.run([command, *command_args], stdout=database_file)
#             database_file.close()
# 
#             database_file = database_filename.open('r')
#             print(database_file.read())
# 
#     def create_tarball(tmp_dir):
#         # 2018.05.04.14.00.03.tar.gz
# 
#         current_time = datetime.now()
#         tarball_name = current_time.strftime('%Y.%m.%d.%H.%m.%S') + '.tar.gz'
# 
#         tmp_dir = PosixPath(tmp_dir)
#         tarbal_filename = tmp_dir / tarball_name
# 
#         tarball_source = tmp_dir / 'backups'
# 
#         tarball = tarfile.open(tarbal_filename, "w")
#         tarball.add(tarball_source, arcname="backups")
#         tarball.close()
# 
#     tmp_dir = TemporaryDirectory()
# 
#     dbs = ['foobar']
#     dump_databases(dbs, 'localhost', 5432, 'sonkun', None, tmp_dir.name)
#     create_tarball(tmp_dir.name)
# 
#     # send it over
#     client = remofile.Client(address, port, token)
#     client.upload_file(tmp_dir.name)
# 
#     tmp_dir.cleanup()

