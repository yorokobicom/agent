# Copyright (C) LIVE INTERACTIVE SA - All Rights Reserved
# Yorokobi Agent - Automatic database backups for web applications
#
# The source code is proprietary and confidential. Unauthorized copying
# of this file, via any medium, is strictly prohibited.
#
# Written by Jonathan De Wachter <dewachter.jonathan@gmail.com>, May 2018

from tempfile import TemporaryDirectory
import zmq
from remofile import generate_token

license_keys = {}    # license_key -> [agent_id|agent_id|...]
ongoing_backups = {} # backup_id   -> (agent_id, backup_dir, backup_thread)

def generate_agent_id():
    return 1122334455

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
    return randint(7480, 7490)

def BackupThread(Thread):
    def __init__(self, directory, token, port):
        self.directory = directory 
        self.token = token
        self.port = port
        
        self.server = (self.directory, self.token)

    def run(self):
        self.server.run('localhost', self.port)

def initiate_backup():
    # create a backup_id
    backup_id = generate_backup_id()
    
    # create a temporary directory
    backup_dir = TemporaryDirectory()
    
    # pick an available port
    backup_port = pick_available_port()
    
    # generate a remofile token
    backup_token = generate_token()
    
    # create a backup thread
    backup_thread = BackupThread(backup_dir, backup_token, backup_port)
    
    return backup_id, backup_dir, backup_port, 

    
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
    ongoing_backup_detected = False
    
    for backup_id, backup in ongoing_backups.items():
        if agent_id = backup[0]:
            ongoing_backups = True
    
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
        backup_dir, backup_thread = initiate_backup(agent_id)
        
        backup_thread.start()
        ongoing_backups[backup_id] = (agent_id, backup_dir, backup_thread)
        
        response['backup-id']      = backup_id
        response['remofile-port']  = backup_port
        response['remofile-token'] = backup_token
    else:
        if ongoing_backup_detected:
            response['reason'] = "There's already an ongoing backup associated with this agent."
        else:
            response['reason'] = "The backup request wasn't accepted."

    return response

def handle_cancel_backup_request(request):
    # TODO: to be implemented
    assert request['type'] == 'cancel-backup'
    
    # # agent_id = get_agent_id()
    # # backup_id = get_backup_id()
    # 
    # backup = ongoing_backups.get(backup_id)
    # 
    # if not backup:
    #     print("error, backup doesn't exist")
    #     return
    #     
    # agent_id, backup_dir, _. backup_thread = backup
    # 
    # backup_thread.terminate()
    # backup_dir.cleanup()
    # backup_dir.close()
    # 
    # print("Handle cancel backup request; to be implemented.")
    # response = {}
    # 
    # return response

def handle_terminate_backup_request(request):
    assert request['type'] == 'terminate-backup'
    
    # agent_id = get_agent_id()
    # backup_id = get_backup_id()
    
    backup = ongoing_backups.get(backup_id)
    
    if not backup:
        print("error, backup doesn't exist")
        return
        
    agent_id, backup_dir, _. backup_thread = backup
    
    backup_thread.terminate()
    
    # check backup existence
    # check backup validity
    # transfer backup to actual directory
    # write backup report
    
    backup_dir.cleanup()
    backup_dir.close()
    
    print("Handle terminate license request; to be implemented.")
    response = {}
    
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
