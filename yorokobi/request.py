# Copyright (C) Yorokobi, Inc. - All Rights Reserved
# Yorokobi Agent - Automatic database backups for web applications
#
# The source code is proprietary and confidential. Unauthorized copying
# of this file, via any medium, is strictly prohibited.
#
# Written by Jonathan De Wachter <dewachter.jonathan@gmail.com>, May 2018

from enum import IntEnum
import zmq

Request = IntEnum('Request', [
    'GET_CONFIGURATION',
    'RELOAD_CONFIGURATION',
    'GET_STATUS',
    'BACKUP_NOW',
    'UNREGISTER_AGENT'
])

def do_request(request_type, timeout):
    context = zmq.Context.instance()
    socket = context.socket(zmq.REQ)

    socket.connect("tcp://0.0.0.0:12996")
    socket.send_pyobj(request_type)

    if socket.poll(timeout) & zmq.POLLIN:
        response = socket.recv_pyobj()
    else:
        raise TimeoutError

    socket.disconnect("tcp://0.0.0.0:12996")

    return response

def request_configuration(timeout):
    return do_request({'type' : Request.GET_CONFIGURATION}, timeout)

def request_reload_configuration(config, timeout):
    request = {
        'type'   : Request.RELOAD_CONFIGURATION,
        'config' : config
    }

    return do_request(request, timeout)

def request_status(timeout):
    return do_request({'type' : Request.GET_STATUS}, timeout)

def request_backup_now(timeout):
    return do_request({'type' : Request.BACKUP_NOW}, timeout)

def request_unregister_agent(timeout):
    return do_request({'type' : Request.UNREGISTER_AGENT}, timeout)
