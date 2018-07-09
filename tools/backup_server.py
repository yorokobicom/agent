# Copyright (C) LIVE INTERACTIVE SA - All Rights Reserved
# Yorokobi Agent - Automatic database backups for web applications
#
# The source code is proprietary and confidential. Unauthorized copying
# of this file, via any medium, is strictly prohibited.
#
# Written by Jonathan De Wachter <dewachter.jonathan@gmail.com>, May 2018

import os
from pathlib import PosixPath
from tempfile import TemporaryDirectory
from threading import Thread
import zmq
from remofile import Server, generate_token

license_keys = {}    # license_key -> [agent_id|agent_id|...]
ongoing_backups = {} # backup_id   -> (agent_id, backup)

def generate_agent_id():
    return 1122334455

def is_registered_agent(agent_id):
    for license_key, registered_agents in license_keys.items():
        for registered_agent in registered_agents:
            if agent_id == registered_agent:
                return True

    return False

def generate_backup_id():
    # the logic can be modified to fit backend architecture; it can be
    # unique during lifetime of the service, but the most important is
    # that it doesn't generate a backup ID already in used (see
    # ongoing_backups variable)

    from random import randint
    return randint(1000, 9999)

def pick_available_port():
    # the logic can be modified to fit backend architecture; it should
    # return a port available on the backup server to transfer the
    # backups over with Remofile, and lock it until the transfer is
    # finished

    from random import randint
    return randint(27480, 27490)

def compute_backup_destination(agent_id, backup_id):
    return PosixPath(os.getcwd(), 'agent-{0}'.format(agent_id), 'backup-{0}'.format(backup_id))

def is_backup_valid(agent_id, backup_id):
    # the logic can be modified to accomodate business, here I simply
    # check the directory isn't empty but further check could be made
    # in order to verify backup validity (corrupted backups)
    return True

def detect_ongoing_backup(_agent_id):
    for _, (agent_id, backup) in ongoing_backups.items():
        if _agent_id == agent_id:
            return True

    return False

class BackupThread(Thread):
    def __init__(self, directory, token, port):
        Thread.__init__(self)

        self.directory = directory
        self.token = token
        self.port = port
        print(self.port)
        self.server = Server(directory, token)

    def run(self):
        self.server.run(self.port, '127.0.0.1')

    def terminate(self):
        self.server.terminate()

def initiate_backup(agent_id):
    # create a backup_id
    backup_id = generate_backup_id()

    # create a temporary directory
    backup_dir = compute_backup_destination(agent_id, backup_id)
    backup_dir.mkdir(parents=True, exist_ok=True)

    # pick an available port
    backup_port = pick_available_port()

    # generate a remofile token
    backup_token = generate_token()

    # create a backup thread
    backup_thread = BackupThread(backup_dir, backup_token, backup_port)

    return backup_id, backup_thread

def terminate_backup(backup_id):
    assert backup_id in ongoing_backups

    _, backup = ongoing_backups[backup_id]

    backup.terminate()
    backup.join()

    del ongoing_backups[backup_id]

def handle_register_agent_request(request):
    assert request['type'] == 'register-agent'

    license_key = request['license-key']

    def manual_license_key_accept(license_key):
        print("License key {0} is requested for registration.".format(license_key))
        accept = input("Accept it ? [Y/n]")

        return accept == 'y' or accept == 'Y'

    accept = manual_license_key_accept(license_key)

    response = {}
    response['type'] = 'accepted' if accept else 'refused'

    if accept:
        response['agent-id'] = generate_agent_id()
    else:
        response['reason'] = "The license key wasn't accepted."

    return response

def handle_initiate_backup_request(request):
    assert request['type'] == 'initiate-backup'

    agent_id = request['agent-id']

    # check if there's already an ongoing backup associated to that
    # agent, in this case, the backup is refused
    ongoing_backup_detected = detect_ongoing_backup(agent_id)

    def manual_backup_request_accept(agent_id):
        print("Agent with ID {0} is requesting a backup.".format(agent_id))
        accept = input("Accept it ? [Y/n]")

        return accept == 'y' or accept == 'Y'

    accept = False
    if not ongoing_backup_detected:
        accept = manual_backup_request_accept(agent_id)

    response = {}
    response['type'] = 'accepted' if accept else 'refused'

    if accept:
        backup_id, backup_thread = initiate_backup(agent_id)

        backup_thread.start()
        ongoing_backups[backup_id] = backup_thread

        response['backup-id']      = backup_id
        response['remofile-token'] = backup_thread.token
        response['remofile-port']  = backup_thread.port
    else:
        if ongoing_backup_detected:
            response['reason'] = "There's already an ongoing backup associated with this agent."
        else:
            response['reason'] = "The backup request wasn't accepted."

    return response

def handle_cancel_backup_request(request):
    # the difference with terminate backup request is that it should not
    # check backup validity, mark the backup as cancelled and possibly
    # delete the content (if data were sent over)
    assert request['type'] == 'cancel-backup'

    agent_id = request['agent-id']
    backup_id = request['backup-id']

    # check if agent is registered
    if not is_registered_agent(agent_id):
        response = {}
        response['type'] == 'refused'
        response['message'] = "agent isn't even registered"
        return response

    # check if there's an actual ongoing backup associated to this id
    backup = ongoing_backups.get(backup_id)

    if not backup:
        response = {}
        response['type'] == 'refused'
        response['message'] = "no backup associated to this id"
        return response

    terminate_backup(backup_id)

    # delete the backup directory (and therefore its content)
    backup_dir = compute_backup_destination()
    backup_dir.delete()

    response = {}
    response['type'] = 'accepted'

    return response

def handle_terminate_backup_request(request):
    # it should check for agent and backup id validity, and check for
    # backup vaildity
    assert request['type'] == 'terminate-backup'

    agent_id = request['agent-id']
    backup_id = request['backup-id']

    # check if agent is registered
    if not is_registered_agent(agent_id):
        response = {}
        response['type'] == 'refused'
        response['message'] = "agent isn't even registered"
        return response

    # check if there's an actual ongoing backup associated to this id
    backup = ongoing_backups.get(backup_id)

    if not backup:
        response = {}
        response['type'] == 'refused'
        response['message'] = "no backup associated to this id"
        return response

    # check if we accept the backup; check for backup existency and
    # validity
    if not is_backup_valid(agent_id, backup_id):
        terminate_backup(backup_id)

        response = {}
        response['type'] == 'refused'
        response['message'] = "backup not accepted, failure, terminating bakcup"
        return response

    terminate_backup(backup_id)
    backup_thread.terminate()

    response = {}
    response['type'] == 'accepted'

    return response

def handle_request(request):
    request_type = request['type']

    if request_type == 'register-agent':
        return handle_register_agent_request(request)
    elif request_type == 'initiate-backup':
        return handle_initiate_backup_request(request)
    elif request_type == 'cancel-backup':
        return handle_cancel_backup_request(request)
    elif request_type == 'terminate-backup':
        return handle_terminate_backup_request(request)

if __name__ == "__main__":
    context = zmq.Context.instance()

    address = '127.0.0.1'
    port = 6769
    socket_address = 'tcp://{0}:{1}'.format(address, str(port))

    socket = context.socket(zmq.REP)
    socket.bind(socket_address)

    while True:
        if socket.poll(-1) & zmq.POLLIN:
            request = socket.recv_json()
            response = handle_request(request)
            socket.send_json(response)

    socket.unbind(socket_address)
