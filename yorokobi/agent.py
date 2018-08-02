# Copyright (C) LIVE INTERACTIVE SA - All Rights Reserved
# Yorokobi Agent - Automatic database backups for web applications
#
# The source code is proprietary and confidential. Unauthorized copying
# of this file, via any medium, is strictly prohibited.
#
# Written by Jonathan De Wachter <dewachter.jonathan@gmail.com>, May 2018

import schedule
import zmq
from yorokobi.configuration import BACKUP_HOSTNAME, BACKUP_PORT
from yorokobi.configuration import load_configuration, save_configuration
from yorokobi.license import identify_agent
from yorokobi.database import configure_databases
from yorokobi.backup import Backup

AGENT_ADDRESS = 'tcp://0.0.0.0:6996' # 'inproc://yorokobi-agent'

from yorokobi.request import Request
from yorokobi.request import request_reload_configuration
from yorokobi.request import request_get_status

class Agent:
    """ Yorokobi agent running in the background.

    The agent listens to the front-end CLI requests (using IPC on
    address 'inproc://yorokobi-agent') and works with the backup server
    to authenticate the agent and send backups over.

    It must be constructed with the agent configuration and a logger.
    The configuration contains essential information such as the backup
    server address and port, the database credentials (host, port,
    username, password) and the list of databases to backup. The logger
    allows one to keep track of the agent activity.

    The agent enters the main loop when the blocking run() method is
    called and must be stopped with the terminate() method called
    asynchronously.

    When the agent is running, it's either backing up or not backing up.
    When there is an ongoing backup, an external thread in launched.
    """

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger

        self.config_filename = None

        self.running = False

        # compute internal and external socket addresses
        self.internal_socket_address = AGENT_ADDRESS
        self.external_socket_address = 'tcp://{0}:{1}'.format(BACKUP_HOSTNAME, str(BACKUP_PORT))

        # backing up state related attribute
        self.backup = None

    def __del__(self):
        pass
#        # if there is an ongoing backup, exit graciously
#        if self.backup:
#            self.backup.cancel_and_wait()

    def get_status(self):
        response = {}

        response['next-backup-time'] = schedule.next_run()

        return response

    def reload_configuration(self):
        try:
            config_file = self.config_filename.open('r')
            new_config = load_configuration(config_file)
            config_file.close()
        except Exception as err:
            print("An error occured during reloading the configuration file")
            return None

        def perform_config_change(new_config):
          # TODO: do config update according to current agent state (for
          # example, what if the agent is in the middle of a backup, what
          # behvior should we expect)
          self.config = new_config

        perform_config_change(new_config)

        return self.config

    def backup_now(self):
        accepted = self.initiate_backup()
        print('backup-now: accepted')
        return accepted

    def run(self):
        self.setup_scheduler()
        self.initialize_sockets()
        self.loop()
        self.terminate_sockets()

    def setup_scheduler(self):
        def scheduler_job():
            # will request a backup and do it if the conditions are
            # satisfied
            self.initiate_backup()

        schedule.every().wednesday.at("13:15").do(scheduler_job)

    def initialize_sockets(self):
        context = zmq.Context()

        self.internal_socket = context.socket(zmq.REP)
        self.internal_socket.bind(self.internal_socket_address)

        self.external_socket = context.socket(zmq.REQ)
        self.external_socket.connect(self.external_socket_address)

    def terminate_sockets(self):
        self.external_socket.disconnect(self.external_socket_address)
        self.internal_socket.unbind(self.internal_socket_address)

    def process_internal_socket(self):
        try:
            request = self.internal_socket.recv_pyobj(zmq.DONTWAIT)
        except zmq.Again:
            return
        print(request)
        if request == Request.GET_STATUS:
            response = self.get_status()
        elif request == Request.RELOAD_CONFIGURATION:
            response = self.reload_configuration()
        elif request == Request.BACKUP_NOW:
            response = self.backup_now()

        print(response)
        self.internal_socket.send_pyobj(response)

    def process_external_socket(self):
        pass

    def process_scheduler(self):
        schedule.run_pending()

    def process_backup(self):
        # nothing to do if there is no ongoing backup
        if not self.backup:
            return

        # if the ongoing backup is terminated, send a terminate backup
        # signal to the backup server
        if not self.backup.is_alive():
            request = {}
            request['type'] = 'terminate-backup'
            request['agent-id'] = self.config['agent-id']
            request['backup-id'] = self.backup.backup_id

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
        self.config['agent-id'] = 42

        request = {}
        request['type'] = 'initiate-backup'
        request['agent-id'] = self.config['agent-id']

        self.external_socket.send_json(request)

        if self.external_socket.poll(10000) & zmq.POLLIN: #TODO: replace timeout value
            response = self.external_socket.recv_json()
        else:
            raise TimeoutError

        response_type = response['type']

        # don't intiate a backup if the backup server didn't accept it
        if response_type == 'refused':
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
            self.process_internal_socket()
            self.process_external_socket()
            self.process_scheduler()
            self.process_backup()

    def terminate(self):
        self.running = False

def print_configuration_file_updated(has_agent_reloaded):
    if has_agent_reloaded:
        print("agent reloadded")
    else:
        print("agent didnt' reload")

# def print_configuration_file_updated(is_agent_reloaded):
    # """ Print configuration file is updated message.

    # The message is different if the agent wasn't running and couldn't
    # reload the configuration file immediatly.

    # If the agent was running, here is the following printed message.

        # Configuration file was successfully updated.

        # The agent just reloaded the new configuration. If you want to
        # check the status of the agent, rerun this command without
        # parameters.

          # sudo yorokobi

        # Visit yorkobi.com for more information.

    # If the agent wasn't running, here is the following printed message.

        # Configuration file was successfully updated.

        # The agent doesn't appear online but don't worry, it will pick the
        # new configuration next next it runs. Perhaps you want to type.

          # sudo systemctl start yorokobi-agent

        # Visit yorkobi.com for more information.

    # Long description.
    # """

    # print("Configuration file was successfully updated.")

    # if is_agent_reloaded:
        # print("The agent just reloaded the new configuration. If you want to check the status of the agent, rerun this command without parameters.")
    # else:
        # print("The agent doesn't appear online but don't worry, it will pick the new configuration next next it runs. Perhaps you want to type.")

    # command = "sudo yorokobi" if is_agent_reloaded else "sudo systemctl start yorokobi-agent"
    # print(command)

    # print("All set! Enjoy some peace of mind. Your backups will begin soon.")
    # print("Visit yorkobi.com for more information.")

def configure_agent(config_filename, config, change_license, reconfigure_dbs):
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

    # ask if the user wants to the save the new settings, and update the
    # configuration file if yes
    save_settings = input("Save settings? [y/N]")
    are_settings_saved = False

    if save_settings == 'y' or save_settings == 'Y':
        try:
            config_file = config_filename.open('w')
        except:
            print("Failed to save the configuration file; cannot open it in write mode")
            exit(1)

        try:
            save_configuration(config_file, config)
        except:
            print("Failed to save the configuration file")
            exit(1)

        config_file.close()

        are_settings_saved = True

    # reload the agent to pick the new configuration file, and print an
    # update message
    if are_settings_saved:
        has_agent_reloaded = True

        try:
            loaded_config = request_reload_configuration(1000)

            # TODO: check if the returned loaded config by the agent is
            # the same as the one we have
            # assert loaded_config == config

        except TimeoutError:
            has_agent_reloaded = False

        print_configuration_file_updated(has_agent_reloaded)

def show_agent_status():
    print("show-agent-status")
    is_agent_connected = True

    try:
        status = request_get_status(1000)
    except TimeoutError:
        is_agent_connected = False

    if is_agent_connected:
        print("display agent status")
        print(status)
    else:
        print("print that the agent isn't connected or couldn't be reached")

def reset_agent():
    pass
