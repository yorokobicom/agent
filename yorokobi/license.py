# Copyright (C) LIVE INTERACTIVE SA - All Rights Reserved
# Yorokobi Agent - Automatic database backups for web applications
#
# The source code is proprietary and confidential. Unauthorized copying
# of this file, via any medium, is strictly prohibited.
#
# Written by Jonathan De Wachter <dewachter.jonathan@gmail.com>, May 2018

import zmq
from yorokobi.configuration import BACKUP_HOSTNAME, BACKUP_PORT

def register_agent(license_key):
    """ Register the agent with a given license key.
    
    This function connnect to the backup server in order to register 
    an agent with a license key. If the operation is successful, an 
    agent identifier is returned, otherwise an explicit error message 
    is returned.
    """
    
    context = zmq.Context.instance()

    socket_address = 'tcp://{0}:{1}'.format(BACKUP_HOSTNAME, BACKUP_PORT)
    socket = context.socket(zmq.REQ)

    socket.connect(socket_address)

    request = {
        'type' : 'register-agent',
        'license-key' : license_key,
    }
    
    socket.send_json(request)
    response = socket.recv_json()

    socket.disconnect(socket_address)

    if response['type'] == 'accepted':
        return response['agent-id'], None
    elif response['type'] == 'refused':
        return None, response['reason']

def identify_agent(config):
    """ Enter license command-line work-flow.

    Long description.

    Enter your License Key below:
    License Key: SKSICNALASCMASKCKASMCJDFVJFJFJV

    Long description.

    Please wait, attempting to authenticate your license...
    Success. Your license key worked fine :-)

    Long description.

    ERROR: The License key given does not exist in our records.
    Retry configuration? [Y/n]

    Long description.
    """

    print(config['license-key'])
    print(config['agent-id'])
    assert config['license-key'] == None
    assert config['agent-id']    == None

    is_agent_identified = False

    while not is_agent_identified:
        # show enter license key message, and get user input
        print("Enter your license Key below.")
        license_key = input("License key: ")

        print("Please wait, attempting to authenticate your license...")
        agent_id, error_message = register_agent(license_key)
            
        if agent_id:
            # show license is valid message
            print("Success. Your license key worked fine :-)")
            
            # update the config values with valid license key and the 
            # returned agent identifier
            config['license-key'] = license_key
            config['agent-id']    = agent_id
            
            is_agent_identified = True

        else:
            # show license not valid error message, and get user input
            print("The License key given does not exist in our records.")
            print("error message returned is: {0}".format(error_message)) # TODO
            retry = input("Retry? [Y/n]")

            if retry != 'y' and retry != 'Y':
                break
