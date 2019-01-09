# Copyright (C) Yorokobi, Inc. - All Rights Reserved
# Yorokobi Agent - Automatic database backups for web applications
#
# The source code is proprietary and confidential. Unauthorized copying
# of this file, via any medium, is strictly prohibited.
#
# Written by Jonathan De Wachter <dewachter.jonathan@gmail.com>, May 2018

import socket
import zmq
import requests
from requests.auth import HTTPBasicAuth

def register_agent(license_key):
    """ Register the agent with a given license key.

    This function connnect to the backup server in order to register
    an agent with a license key. If the operation is successful, an
    agent identifier is returned, otherwise an explicit error message
    is returned.
    """

	# Examples of responses (accepted vs refused):
	#
	# 200 OK
	# {"id":"CCMgmS99JTV7s98kc","hostname":"vulpix","ip_address":"2a02:a03f:5248:9e00:b10c:56da:a766:f7f3","active":true}
	#
	# 401 Unauthorized
	# { "errors": [{ "type": "access_denied", "title": "HTTP Basic: Access denied." }] }

    auth = HTTPBasicAuth(license_key, '')

    params = {
        'hostname'  : socket.gethostname(),
        'ip_address': socket.gethostbyname(socket.gethostname())
	}

    response = requests.post("https://api.yorokobi.com/v1/agents", data=params, auth=auth)

    if response.status_code == 200:
        return response.json()['id'], None
    else:
        return None, response.text

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

    assert config['license-key'] == None or config['agent-id']    == None

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
