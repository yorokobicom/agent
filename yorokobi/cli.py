import os.path
from pathlib import PosixPath
import click
from yorokobi.configuration import get_default_filename, get_default_configuration
from yorokobi.configuration import load_configuration, save_configuration
from yorokobi.agent import Agent
from yorokobi.agent import configure_agent, reset_agent
from yorokobi.agent import show_agent_status
from yorokobi.agent import show_agent_logs
from yorokobi.request import request_configuration, request_reload_configuration
from yorokobi.request import request_backup_now, request_unregister_agent

def print_logo():
    logo = r"""
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

TIMEOUT = 10000

LOG_ERROR_MSG           = "An error occured during the setup of the logger phase."
CONFIGURATION_ERROR_MSG = "An error occured during the loading configuration file phase."
CONNECTION_ERROR_MSG    = "Foobar"

@click.group()
def cli():
    pass

@click.command()
@click.option('--conf', default=os.path.join(os.getcwd(), 'yorokobi.conf'))
@click.option('--log',  default=os.path.join(os.getcwd(), 'yorokobi.log'))
def run_agent(conf, log):
    """ Start the agent in the background.

    This command starts the agent in the background after it initiates
    the logger to use a log file and loads the configuration file. The
    agent runs indefinitively until it's explicitly terminated.

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

    config_filename = PosixPath(conf)
    log_filename = PosixPath(log)

    # load the configuration file (use default configuration values if
    # it doesn't exist)
    if config_filename.exists():
        config_file = config_filename.open('r')
        config = load_configuration(config_file)
        config_file.close()
    else:
        config = get_default_configuration()
        config_file = config_filename.open('w+')
        save_configuration(config_file, config)
        config_file.close()

    # print startup message
    print("The Yorokobi agent is starting.", end="\n\n")
    print("Configuration file is '{0}'".format(str(config_filename)))
    print("Log file is '{0}'".format(str(log_filename)), end="\n\n")

    # create the agent instance and start its main loop
    agent = Agent(config, config_filename, log_filename)
    agent.run()

    # print 'successfully stopped agent' message
    print('The Yorokobi agent has succesfully stopped')

@cli.command("setup")
@click.option('--change-license')
@click.option('--reconfigure-dbs')
@click.option('--reset-all')
def setup_agent(change_license, reconfigure_dbs, reset_all):
    """ Configure the agent or show its status.

    This command starts the command-line configuration process of the
    agent if it's not fully configured yet, or shows current the agent
    status. It also suggests the use of the --reset-all,
    --change-license and --reconfigure-dbs flags.

    If the --change-license flag is passed, the user is asked to
    re-enter the license key, re-identifying the agent with a different
    agent ID.

    If the --reconfigure-dbs flag is passed, the user is given the
    ability to change the database credentitials and reselect the
    databases to backup.

    With the --reset-all flag, you can erase the current configuration
    and start from scratch again. It will ask the user if they want to
    reconfigure it now.
    """

    # ask the agent (running in the background) its current
    # configuration
    try:
        config = request_configuration(TIMEOUT)
    except TimeoutError:
        print("The agent doesn't appear running; ensure the agent is started.")
        exit(1)

    # use default connfiguration values if the --reset-all flag is
    # passed
    if reset_all:
        config = get_default_configuration()

    # check if the agent still needs to be configured, or if it's
    # explicitely requested to be reconfigured
    def is_agent_identified(config):
        return config['license-key'] != None and config['agent-id'] != None

    def is_database_configured(config):
        return config['selected-dbs'] != None

    change_license  = change_license  or not is_agent_identified(config)
    reconfigure_dbs = reconfigure_dbs or not is_database_configured(config)

    # if the agent isn't fully configured (or requested to be
    # reconfigured), configure it, otherwise show the agent status
    if change_license or reconfigure_dbs:
        print_logo()
        print("Welcome to Yorokobi. For more information please visit www.yorokobi.com.", end="\n\n")
        configure_agent(config, change_license, reconfigure_dbs)
    else:
        show_agent_status()

@click.command("backup")
def backup_now():
    """ Initiate a backup request.

    This command manually initiates a backup. Description of this
    command is to be written.
    """

    # 1. the agent could not be reached
    # 2. the backup has been accepted and initated (show stats)
    # 3. the backup fails to start (show reason, include 'not configured agentn')

    try:
        accepted = request_backup_now(TIMEOUT)
    except TimeoutError:
        print("The agent doesn't appear running; ensure the agent is started.")
        exit(1)

    if accepted:
        print("Backup started. Visit your dashboard at www.yorokobi.com to see its progress.")
    else:
        print("Backup request isn't accepted; for reason X")


@click.command("register")
def register_agent():
    """ Register an agent. """

    pass

@click.command("unregister")
def unregister_agent():
    """ Unregister an agent. """

    try:
        accepted = request_unregister_agent(TIMEOUT)
    except TimeoutError:
        print("The agent doesn't appear running; ensure the agent is started.")
        exit(1)

    if accepted:
        print("Agent was successfully unregistered")
    else:
        print("Agent isn't registered yet.")

@click.command("status")
def get_agent_status():
    """ Get the status of the agent. """

    show_agent_status()

@click.command("logs")
def get_agent_status():
    """ Get the logs of the agent. """

    show_agent_logs()

cli.add_command(setup_agent)
cli.add_command(backup_now)
cli.add_command(register_agent)
cli.add_command(unregister_agent)
cli.add_command(get_agent_status)
