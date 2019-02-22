import time
from multiprocessing import Process
import socket
import requests
from requests.auth import HTTPBasicAuth
from flask import Flask, request, jsonify
import pytest

PORT = 8087

LICENSE_KEY = "M8ddTKx_87Iw2_EPvR9FD8Ol8_MGrqEe0LaGorsAh9Q"
AGENT_ID = "uLPtJZvx4UD0R_lfKf"

def test_agent():

    temporary_directory = TemporaryDirectory()

    config = get_default_configuration()
    config_filename = PosixPath(temporary_directory.name) / 'yorokobi.conf'
    log_filename = PosixPath(temporary_directory.name) / 'yorokobi.log'

    agent = Agent(config, config_filename, log_filename)

    # test if the agent isn't initally registered
    assert agent.is_registered() == False

    # test if the agent doesn't have the databases initially configured
    assert agent.are_databases_configured() == True

    # test that configuration is the same the one initially passed
    assert config == agent.get_configuration()

    # todo: test status here

    # test changing the configuratio of the agent
    config['postgresql-host'] = '127.0.0.1'
    new_config= agent.reload_configuration(config)
    assert new_config == config

    # test registering the agent
    agent_id, error_message = incorrect_license_key = LICENSE_KEY[::-1]

    assert agent_id == None
    assert 'invalid' in error_message

    agent_id, error_message = register_agent(LICENSE_KEY)

    assert agent_id == AGENT_ID
    assert error_message == None

    config['license-key'] = LICENSE_KEY
    config['agent-id'] = AGENT_ID

    agent.reload_configuration(config)
    assert agent.is_registered() == True

    # test configuring the databases
    config['postgresql-user']     = POSTGRESQL_USER
    config['postgresql-password'] = POSTGRESQL_PASSWORD
    config['postgresql-host']     = 'localhost'
    config['postgresql-port']     = POSTGRESQL_PORT
    config['selected-dbs']        = 'all'

    assert agent.are_databases_configured() == True

    # test the agent is doing a backup
    assert agent.backup == None

    agent.initiate_backup()
    assert agent.backup != None

    time.sleep(2)

    agent.process_backup() # update implementation to return boolean
    assert agent.backup == None
