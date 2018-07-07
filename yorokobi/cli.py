# Copyright (C) LIVE INTERACTIVE SA - All Rights Reserved
# Yorokobi Agent - Automatic database backups for web applications
#
# The source code is proprietary and confidential. Unauthorized copying
# of this file, via any medium, is strictly prohibited.
#
# Written by Jonathan De Wachter <dewachter.jonathan@gmail.com>, May 2018

import os.path
from pathlib import PosixPath
import logging
import click
from yorokobi.configuration import get_default_filename, get_default_configuration
from yorokobi.configuration import load_configuration, save_configuration
from yorokobi.agent import Agent
from yorokobi.agent import configure_agent, show_agent_status, reset_agent
from yorokobi.request import request_backup_now

def print_logo():
    logo = """
                                  __                 __
                                 /\ \               /\ \        __
 __  __      ___    _ __    ___  \ \ \/'\      ___  \ \ \____  /\_\
/\ \/\ \    / __`\ /\`'__\ / __`\ \ \ , <     / __`\ \ \ '__`\ \/\ \
\ \ \_\ \  /\ \L\ \\ \ \/ /\ \L\ \ \ \ \\`\  /\ \L\ \ \ \ \L\ \ \ \ \
 \/`____ \ \ \____/ \ \_\ \ \____/  \ \_\ \_\\ \____/  \ \_,__/  \ \_\
  `/___/> \ \/___/   \/_/  \/___/    \/_/\/_/ \/___/    \/___/    \/_/
     /\___/
     \/__/
    """

    print(logo)


LOG_ERROR_MSG           = "Foobar"
CONFIGURATION_ERROR_MSG = "Foobar"
CONNECTION_ERROR_MSG    = "Foobar"

@click.command()
@click.option('--conf', default=os.path.join(os.getcwd(), 'yorokobi.conf'))
@click.option('--log',  default=os.path.join(os.getcwd(), 'yorokobi.log'))
def run_agent(conf, log):
    """ Start the agent in the background.

    This command starts the agent in the background after it initiates
    the logger to use a log file and loads the configuration file. The
    agent etablishes a connection with the server and runs indefinitively
    until it's explicitly terminated.

    The --conf and --log flags allow to change the location (and name)
    of the configuration and log files. By default, it uses
    'yorokobi.conf' and 'yorokobi.log' located in the current working
    directory. The log file is created if it doesn't exist. If the 
    configuration file doens't exist, it uses the default configuration 
    values.

    The agent fails to start if an error occurs during reading the 
    configuration file, if the log file can't be created or if the 
    connection with the backup server can't be etablished.
    """
    
    # load the configuration file (use default configuration values if 
    # it doesn't exist)
    config_filename = PosixPath(conf)
    
    if config_filename.exists():
        try:
            config_file = config_filename.open('r')
            config = load_configuration(config_file)
            config_file.close()
        except Exception as excp:
            print(excp)
            print(CONFIGURATION_ERROR_MSG)
            exit(1)
    else:
        config = get_default_configuration()

    print(config)
    
    # configure the logger with the log file
    logger = logging.getLogger('yorokobi')

    try:
        file_handler = logging.FileHandler(log)
    except IOError:
        print(LOG_ERROR_MSG)
        exit(1)

    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.FileHandler(log)
    console_handler.setLevel(logging.ERROR)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # print 'starting the agent' log message
    logger.warning("The Yorokobi agent is starting with configuration file '{0}' and log file {1}".format(conf, log))

    # create the agent instance and start its main loop
    agent = Agent(config, logger)
    agent.config_filename = config_filename

    try:
        agent.run()
    except Exception: # connection problem
        pass
    except Exception:
        pass

    # print 'successfully stopped agent' log message
    logger.warning('The Yorokobi agent has succesfully stopped')

@click.command()
@click.option('--reset-all')
@click.option('--change-license')
@click.option('--reconfigure-dbs')
def yorokobi_cli(reset_all, change_license, reconfigure_dbs):
    """ Configure the agent or show its status.

    This command starts the command-line configuration process of the
    agent if it's not fully configured yet, or shows current the agent 
    status. It also suggests the use of the --reset-all, 
    --change-license and --reconfigure-dbs flags.

    If the --change-license flag is passed, the user is asked to
    re-enter the license key, re-identifying the agent with a different 
    identifier.

    If the --reconfigure-dbs flag is passed, the user is given the
    ability to change the database credentitials and reselect the
    databases to backup.
    
    With the --reset-all flag, you can erase the current configuration 
    and start from scratch again. It will ask the user if they want to 
    reconfigure it now.
    """
    
    # # get default path of the configuration file
    # config_filename = get_default_filename()
    # 
    # # read the configuration from the configuration file, or create the 
    # # default configuration if it doesn't exist
    # if not config_filename.exists():
    #     try:
    #         config_file = config_filename.open('w')
    #     except:
    #         print("Failed to load the configuration file; doens't exist and unable to create it")
    #         exit(1)
    # 
    #     config = get_default_configuration()
    #     save_configuration(config_file, config)
    #     config_file.close()
    # else:
    #     try:
    #         config_file = config_filename.open('r')
    #     except:
    #         print("Failed to load the configuration file; cannot open it")
    #         exit(1)
    # 
    #     try:
    #         config = load_configuration(config_file)
    #     except:
    #         print("Failed to load the configuration file; no valid data found")
    #         exit(1)
    # 
    # # use default connfiguration values if the --reset-all flag is
    # # passed
    # if reset_all:
    #     config = get_default_configuration()
    # 
    # # check if the agent still needs to be configured, or if it's 
    # # explicitely requested to be reconfigured
    # def is_agent_identified(config):
    #     return config['license-key'] != None and config['agent-id'] != None
    # 
    # def is_database_configured(config):
    #     return config['selected-dbs'] != None
    # 
    # change_license  = change_license  or not is_agent_identified(config)
    # reconfigure_dbs = reconfigure_dbs or not is_database_configured(config)
    # 
    # # if the agent isn't fully configured (or requested to be 
    # # reconfigured), configure it, otherwise show the agent status
    # if change_license or reconfigure_dbs:
    #     configure_agent(config_filename, config, change_license, reconfigure_dbs)
    # else:
    #     print("show-agent-status")
    #     # show_agent_status(config)

    print("show-agent-status")
    show_agent_status()
    
@click.command()
def backup_now():
    """ Initiate a backup request.

    This command manually initiates a backup. Description of this
    command is to be written.
    """

    # 1. the agent could not be reached
    # 2. the backup has been accepted and initated (show stats)
    # 3. the backup fails to start (show reason, include 'not configured agentn')

    accepted = request_backup_now(10000)
    
    if accepted:
        print("backup request accepted; starting now")
    else:
        print("backup request isn't accepted; for reason X")
        
