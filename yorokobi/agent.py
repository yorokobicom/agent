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
from yorokobi.configuration import save_configuration
from yorokobi.license import identify_agent
from yorokobi.database import configure_databases

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
        self.backing_up = False
        self.backup_thread = None
        # self.update_thread = None
        
    def get_status(self):
        response = {}
        
        response['next-backup-time'] = schedule.next_run()
        
        return response
        
    def reload_configuration(self):        
        print("agent is reloading the following file: " + str(elf.config_filename))
        
        config_file = self.config_filename.open('r') 
        new_config = load_configuration(config_file)
        config_file.close()
        
        # do the actual change # TODO: perform config update according to the agent state
        # def perform_config_change(new_config):
            # pass
            
        # perform_config_change(new_config)
            
        self.config = new_config
        
        # return new_config
        return new_config
    
    def backup_now(self):
        # if in the middle of backing up, says no
        # if not backing up, says yes
        # if initiating backing up and it fails, send back why
        print("Handle backup now request; to be implemented.")
        
        response = {}
        response['type']    = 'accepted'
        response['message'] = 'backup-now'
        
        return response

    def run(self):
        self.setup_scheduler()
        self.initialize_sockets()
        self.loop()
        self.terminate_sockets()

    def setup_scheduler(self):
        def scheduler_job():
            print("do initiate backup")
            
        schedule.every().wednesday.at("13:15").do(scheduler_job)
        
    def initialize_sockets(self):
        context = zmq.Context.instance()
        
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
        
        if request == Request.GET_STATUS:
            response = self.get_status()
        elif request == Request.RELOAD_CONFIGURATION:
            response = self.reload_configuration()
        elif request == Request.BACKUP_NOW:
            response = self.backup_now()

        self.internal_socket.send_pyobj(response)
        
    def process_external_socket(self):
        pass

    def process_scheduler(self):
        schedule.run_pending()

    def process_backup(self):
        pass
        # if not self.is_backingup:
        #     return
        #     
        # assert self.backup_thread != None
        # 
        # if self.backup_thread.is_terminated():
        #     self.is_backingup = False
        
    def initiate_backup(self):
        pass
        
    def cancel_ongoing_backup(self):
        assert self.is_backingup  == True
        assert self.backup_thread != None
        
        # send signal to thread
        # wait until it's terminated
        
        self.backup_thread = None
        self.is_backingup  = True
        
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
            assert loaded_config == config
            
        except TimeoutError:
            has_agent_reloaded = False
        
        print_configuration_file_updated(has_agent_reloaded)

def show_agent_status():
    try:
        agent_status = request_get_status(1000)
    except TimeoutError:
        print("cannot connect agent")
        return
        
    print(agent_status)
    
def reset_agent():
    pass
