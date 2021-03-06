import time
import logging
import socket
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
from yorokobi.request import request_logs

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

    def __init__(self, config, config_filename, logs_filename):
        self.config = config

        self.config_filename = config_filename
        self.logs_filename = logs_filename

        # configure the logger with the log file
        self.logger = logging.getLogger('yorokobi')
        self.logger.setLevel(logging.DEBUG)

        try:
            file_handler = logging.FileHandler(logs_filename)
        except IOError:
            print("Can't create the agent log file")
            exit(1)

        file_handler.setLevel(logging.DEBUG)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.ERROR)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        self.running = False

        # backing up state related attribute
        self.backup = None

    def __del__(self):
        pass
#        # if there is an ongoing backup, exit graciously
#        if self.backup:
#            self.backup.cancel_and_wait()

    def is_registered(self):
        return self.config['license-key'] and self.config['agent-id']

    def are_databases_configured(self):
        return self.config['selected-dbs'] != None

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
        """ Compute the agent status. """

        self.logger.info("Retrieving status..")

        license_key = self.config['license-key']

        if license_key:
            self.logger.info("Detected license key was: {0}".format(license_key))

            agent_id = self.config['agent-id']
            assert agent_id != None

            self.logger.info("Detected agent ID was: {0}".format(agent_id))

            last_backup_time = 0
            next_backup_time = schedule.next_run()
            self.logger.info("Detected next run is for {0}".format(next_backup_time))

        else:
            self.logger.info("No license was detected")

            agent_id = None
            last_backup_time = 0
            next_backup_time = 0

        return license_key, agent_id, last_backup_time, next_backup_time

    def get_logs(self):
        """ Compute the agent logs. """

        logs_file = self.logs_filename.open('r')
        logs = logs_file.readlines()
        logs_file.close()

        return logs

    def backup_now(self):
        self.logger.info("A manual backup is requested")

        accepted = self.initiate_backup()

        if accepted:
            self.logger.info("The backup request was accepted")
        else:
            self.logger.info("The backup was NOT accepted")

        return accepted

    def unregister_me(self):
        """ Unregister the agent.

        Long descripiton here.
        """

        self.logger.info("An unregister agent request was detected")

        # can't unregister an agent that isn't registered
        if not self.is_registered():
            self.logger.info("Can't unregister the agent if it's not registered")
            return False

        # can't unregister an agent in the middle of a backup
        if self.backup:
            self.logger.info("Can't unregister the agent when in the middle of a backup")
            return False

        license_key = self.config['license-key']
        agent_id = self.config['agent-id']
        assert license_key != None and agent_id != None

        # send a unregister agent request to Yorokobi server
        # example of response: None
        self.logger.info("Sending an unregister agent request to Yorokobi server")

        auth = HTTPBasicAuth(license_key, '')
        response = requests.delete("https://api.yorokobi.com/v1/agents/{0}".format(agent_id), auth=auth)

        if response.status_code != 200:
            self.logger.info("Got a negative response from server; an error occured during the unregistration")
            # todo: log error message returned from server
            return False

        # update the current configuration
        self.config['license-key'] = None
        self.config['agent-id'] = None
        self.reload_configuration(self.config)

        return True

    def run(self):
        self.logger.info("Agent has successfull started")

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

        self.logger.info("The agent received a {0} request".format(str(request)))

        if request['type'] == Request.GET_CONFIGURATION:
            response = self.get_configuration()
        elif request['type'] == Request.RELOAD_CONFIGURATION:
            response = self.reload_configuration(request['config'])
        elif request['type'] == Request.GET_STATUS:
            response = self.get_status()
        elif request['type'] == Request.GET_LOGS:
            response = self.get_logs()
        elif request['type'] == Request.BACKUP_NOW:
            response = self.backup_now()
        elif request['type'] == Request.UNREGISTER_AGENT:
            response = self.unregister_me()

        self.socket.send_pyobj(response)

    def process_scheduler(self):
        schedule.run_pending()

    def process_backup(self):
        """ Process the ongoing backup.

        Check if the ongoing backup is terminated. If it is, a signal is
        sent to the backup server and the agent is revert to normal
        state.
        """

        # nothing to do if there is no ongoing backup
        if not self.backup:
            return

        # if the ongoing backup is terminated, send a terminate backup
        # signal to the backup server
        if not self.backup.is_alive():
            self.logger.info("The ongoing backup is detected as terminated; terminating the backup")

            # send a terminate backup signal to the backup server
            # example of response: unknown
            self.logger.info("Sending a terminate backup request to Yorokobi server")

            license_key = self.config['license-key']
            agent_id = self.config['agent-id']
            assert license_key != None and agent_id != None

            backup_id = self.backup.backup_id

            auth = HTTPBasicAuth(license_key, '')

            response = requests.post("https://api.yorokobi.com/v1/backups/{0}/complete".format(backup_id), auth=auth)

            self.logger.info("Response status is {0}".format(response.status_code))
            self.logger.info("Response data is:")
            self.logger.info(response.json())

            if not response.status_code == 200:
                self.logger.error("Got a negative response from server; don't know what to do!")

            self.logger.info("Clean up and remove the backup thread")
            self.backup = None

    def initiate_backup(self):
        """ Initiate a backup.

        This method attempts to start a backup. It fails if the agent
        isn't registered or if the agent is the middle of a backup or if
        the backup server doens't accept it.
        """

        # don't initiate a backup if the agent isn't registered
        if not self.is_registered():
            self.logger.info("Can't initiate a backup because the agent isn't registered")
            return False

        # don't initiate a backup if databases aren't configured
        if not self.are_databases_configured():
            self.logger.info("Can't initiate a backup because no database was configured")
            return False

        # don't initiate a backup if already in the middle of a backup
        if self.backup:
            self.logger.info("Can't initiate a backup because the agent is already in the middle of a backup")
            return False

        license_key = self.config['license-key']
        agent_id = self.config['agent-id']

        assert license_key != None and agent_id != None

        # send a backup request to the Yorokobi server
        # example of response: {"id":"xgh6VzTVsWRa9BnOUqaL","hostname":null,"port":75725,"token":"xgh6VzTVsWRa9BnOUqaL","state":"initial"})
        self.logger.info("Sending a backup request to Yorokobi server")
        auth = HTTPBasicAuth(license_key, '')

        params = {
            'agent_id'  : agent_id,
            'hostname'  : socket.gethostname(),
            'ip_address': socket.gethostbyname(socket.gethostname())
        }

        self.logger.info("Request data is {0}".format(str(params)))
        response = requests.post("https://api.yorokobi.com/v1/backups", data=params, auth=auth)

        self.logger.info("Response status is {0}".format(response.status_code))
        self.logger.info("Response data is:")
        self.logger.info(response.json())

        # don't intiate a backup if the backup server didn't accept it
        if response.status_code != 200:
            self.logger.info("Got a negative response from server; backup was either refused or an error occured")
            # todo: log error message returned from server
            return False

        self.logger.info("Got a positive response from server; backup was accepted")

        # initiate the backup
        self.logger.info("Reading response to retrieve the backup ID, the remofile port and the remofile token")
        backup_id      = response.json()['id']
        remofile_port  = response.json()['port']
        remofile_token = response.json()['token']

        self.logger.info("Backup ID is {0}".format(backup_id))
        self.logger.info("Remofile port is {0}".format(remofile_port))
        self.logger.info("Remofile token is {0}".format(remofile_token))

        self.logger.info("Starting a backup in external thread".format(backup_id))
        self.backup = Backup(backup_id, remofile_port, remofile_token, self.config, self.logger)
        self.backup.start()

        return True

    def cancel_ongoing_backup(self):
        """ Cancel the ongoing backup.

        This method forces termination of an ongoing backup (if any). It
        destroys the underlying backup thread and send a signal to the
        server before putting the agent back to normal state.
        """

        # do nothing if there is no ongoing backup
        if self.backup:
            self.logger.info("Can't cancel an ongoing backup if there is none")
            return

        # send signal to thread and wait until it terminates
        self.logger.info("Terminating the backup thread")
        self.backup.cancel_and_wait()
        self.logger.info("Backup thread terminated")

        # send a terminate backup signal to the backup server
        # example of response: {"id":"xgh6VzTVsWRa9BnOUqaL","hostname":null,"port":75725,"token":"xgh6VzTVsWRa9BnOUqaL","state":"canceled"}
        self.logger.info("Sending a cancel backup request to Yorokobi server")

        license_key = self.config['license-key']
        agent_id = self.config['agent-id']
        assert license_key != None and agent_id != None

        auth = HTTPBasicAuth(license_key, '')
        response = requests.delete("https://api.yorokobi.com/v1/backups/" + self.backup.backup_id, auth=auth)

        self.logger.info("Response status is {0}".format(response.status_code))
        self.logger.info("Response data is:")
        self.logger.info(response.json())

        if not response.status == 200:
            self.logger.error("Got a negative response from server; don't know what to do!")

        self.logger.info("Clean up and remove the backup thread")
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

Visit www.yorokobi.com for more information.
        """

        print(message)

def show_agent_status():
    is_agent_connected = True

    try:
        status = request_status(1000)
    except TimeoutError:
        is_agent_connected = False

    if is_agent_connected:
        license_key, agent_id, last_backup_time, next_backup_time = status

        print("The agent is running. Next backup is scheduled to run in {0}".format(next_backup_time))
    else:
        print("The agent isn't running. Please start it first.")

def show_agent_logs():
    def build_logs_page(logs):
        logs_page = ""
        for logs_line in logs:
            logs_page = logs_page + logs_line

        return logs_page

    is_agent_connected = True

    try:
        logs = request_logs(1000)
    except TimeoutError:
        is_agent_connected = False

    if is_agent_connected:
        logs_page = build_logs_page(logs)

        import pydoc
        pydoc.pager(logs_page)
    else:
        print("The agent isn't running. Please start it first.")

def reset_agent():
    raise NotImplementedError
