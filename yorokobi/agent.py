# Copyright (C) LIVE INTERACTIVE SA - All Rights Reserved
# Yorokobi Agent - Automatic database backups for web applications
#
# The source code is proprietary and confidential. Unauthorized copying
# of this file, via any medium, is strictly prohibited.
#
# Written by Jonathan De Wachter <dewachter.jonathan@gmail.com>, May 2018

import time
import schedule
import zmq
import requests
from requests.auth import HTTPBasicAuth
from yorokobi.configuration import load_configuration, save_configuration
from yorokobi.license import identify_agent
from yorokobi.database import configure_databases
from yorokobi.backup import Backup
from yorokobi.request import Request
from yorokobi.request import request_reload_configuration
from yorokobi.request import request_status

class Agent:
    """ Yorokobi agent running in the background.

    The agent listens to the front-end CLI requests (using IPC on
    address 'ipc://yorokobi-agent') and works with the backup server
    to authenticate the agent and send backups over.

    It must be constructed with the agent configuration and a logger.
    The configuration contains essential information such as the backup
    server address and port, the database credentials (host, port,
    username, password) and the list of databases to backup. The logger
    allows one to keep track of the agent activity.

    The agent enters the main loop when the blocking run() method is
    called and must be stopped with the terminate() method called
    asynchronously (from a different thread).

    When the agent is running, it's either backing up or not backing up.
    When there is an ongoing backup, an external thread in launched.
    """

    def __init__(self, config, config_filename, logger):
        self.config = config
        self.config_filename = config_filename

        self.logger = logger

        self.running = False

        # backing up state related attribute
        self.backup = None

    def __del__(self):
        pass
#        # if there is an ongoing backup, exit graciously
#        if self.backup:
#            self.backup.cancel_and_wait()

    def get_configuration(self):
        return self.config

    def reload_configuration(self, config):

        def perform_config_change(new_config):
          # TODO: do config update according to current agent state (for
          # example, what if the agent is in the middle of a backup, what
          # behvior should we expect)
          self.config = new_config

        perform_config_change(config)

        try:
            config_file = self.config_filename.open('w+')
            save_configuration(config_file, config)
            config_file.close()
        except Exception as e:
            print(e)
            print("An error occured during reloading the configuration file")
            return None

        return self.config

    def get_status(self):
        response = {}

        response['next-backup-time'] = schedule.next_run()

        return response

    def backup_now(self):
        accepted = self.initiate_backup()
        print('backup-now: accepted')
        return accepted

    def run(self):
        context = zmq.Context()

        self.socket = context.socket(zmq.REP)
        self.socket.bind("tcp://0.0.0.0:12996")

        self.setup_scheduler()
        self.loop()

        self.socket.unbind("tcp://0.0.0.0:12996")

    def setup_scheduler(self):
        def scheduler_job():
            # will request a backup and do it if the conditions are
            # satisfied
            self.initiate_backup()

        schedule.every().wednesday.at("13:15").do(scheduler_job)

    def process_socket(self):
        try:
            request = self.socket.recv_pyobj(zmq.DONTWAIT)
        except zmq.Again:
            return

        if request['type'] == Request.GET_CONFIGURATION:
            response = self.get_configuration()
        elif request['type'] == Request.RELOAD_CONFIGURATION:
            response = self.reload_configuration(request['config'])
        elif request['type'] == Request.GET_STATUS:
            response = self.get_status()
        elif request['type'] == Request.BACKUP_NOW:
            response = self.backup_now()

        self.socket.send_pyobj(response)

    def process_scheduler(self):
        schedule.run_pending()

    def process_backup(self):
        # nothing to do if there is no ongoing backup
        if not self.backup:
            return

        # if the ongoing backup is terminated, send a terminate backup
        # signal to the backup server
        if not self.backup.is_alive():

            license_key = config['license-key']
            account_password = config['account-password']
            agent_id = self.config['agent-id']

            auth = HTTPBasicAuth(license_key, account_password)

            params = {
                'agent_id'  : agent_id,
                'hostname'  : socket.gethostname(),
                'ip_address': socket.gethostbyname(socket.gethostname())
            }

            response = requests.post("https://api.yorokobi.co/v1/backups", data=params, auth=auth)
            print(response.status_code)
            print(response.json)

            #
            # if response.status_code == 200:
            #     return response.json['id'], None
            # else:
            #     return None, response.text

            self.external_socket.send_json(request)
            response = self.external_socket.recv_json()

            assert response['type'] == 'accepted'

            self.backup = None

    def initiate_backup(self):
        # attempt to start a backup; it fails if the agent is in the
        # middle of a back-up or if the back-up server doesn't accept it

        # don't initiate a backup if already in the middle of one
        # (should have been cancelled prior to calling this function)
        if self.backup:
            return False

        ## TODO (rework this): the agent should be identified prior to
        ## calling this function
        ## assert self.config['agent-id'] != None
        #if self.config['agent-id'] == None:
        #   print("the agent isn't identified and therefore can't initiate backup")
        #   return False

        license_key = self.config['license-key']
        # account_password = self.config['account-password']
        account_password = 'Nympij-hojbeg-cyxgi5'
        agent_id = self.config['agent-id']

        print("about to initiate a backup")
        print(agent_id)
        print(license_key)
        print(account_password)

        auth = HTTPBasicAuth(license_key, account_password)

        import socket
        params = {
            'agent_id'  : agent_id,
            'hostname'  : socket.gethostname(),
            'ip_address': socket.gethostbyname(socket.gethostname())
        }

        response = requests.post("https://api.yorokobi.co/v1/backups", data=params, auth=auth)
        print(response.status_code)
        print(response.json)

        # don't intiate a backup if the backup server didn't accept it
        if response.status_code != 200:
            return False

        print('aaffa')
        assert response_type == 'accepted'

        backup_id      = response['backup-id']
        remofile_port  = response['remofile-port']
        remofile_token = response['remofile-token']
        print('bbb')
        self.backup = Backup(remofile_port, remofile_token, self.config)
        print('ccc')
        self.backup.start()
        print('ddd')

        return True

    def cancel_ongoing_backup(self):
        # do nothing if there is no ongoing backup
        if self.backup:
            return

        # send signal to thread and wait until it terminates
        self.backup.cancel_and_wait()

        # send a terminate backup signal to the backup server
        request = {}
        request['type'] == 'cancel-backup'
        request['agent-id'] == self.config['agent-id']
        request['backup-id'] == self.backup.backup_id

        self.external_socket.send_json(request) # TODO: do timeout
        response = self.external_socket.recv_json()

        response_type = response['type']
        assert response_type == 'accepted'

        self.backup = None

    def loop(self):
        self.running = True

        while self.running:
            self.process_socket()
            self.process_scheduler()
            self.process_backup()

            time.sleep(0.01)

    def terminate(self):
        self.running = False

def configure_agent(config, change_license, reconfigure_dbs):
    """ Identify the agent and/or configure the database.

    Identify (or re-identify) the agent and/or configure (or
    re-configure) the database. The new configuration values are
    written to the configuration and the agent is reloaded if it's
    running.
    """

    # identify (or re-identify) the agent if needed
    if change_license:
        identify_agent(config)

    # configure (or re-configure) the agent if needed
    if reconfigure_dbs:
        configure_databases(config)

    # ask the user to confirm the new configuration, and send it to the
    # agent so it can reload
    save_settings = input("Save settings? [y/N]")

    if save_settings.lower() == 'y':
        try:
            has_agent_reloaded = request_reload_configuration(config, 100)
        except:
            print("The agent doesn't appear running; ensure the agent is started.")
            exit(1)

        # print a message saying that the agent failed to reload the
        # configuration and suggest the user to contact the support
        if not has_agent_reloaded:
            print("The agent failed to pick up the new configuration.")
            exit(1)

        message = """Configuration was successfully updated.

The agent just reloaded the new configuration. If you want to check
the status of the agent, re-run this command without parameters.

    sudo yorokobi

Visit yorokobi.com for more information.
        """

        print(message)

def show_agent_status():
    is_agent_connected = True

    try:
        status = request_status(1000)
    except TimeoutError:
        is_agent_connected = False

    if is_agent_connected:
        next_backup_time = status['next-backup-time']
        print("The agent is running. Next backup is scheduled to run in {0}".format(next_backup_time))
    else:
        print("The agent isn't running.")

def reset_agent():
    raise NotImplementedError
