# Copyright (C) LIVE INTERACTIVE SA - All Rights Reserved
# Yorokobi Agent - Automatic database backups for web applications
#
# The source code is proprietary and confidential. Unauthorized copying
# of this file, via any medium, is strictly prohibited.
#
# Written by Jonathan De Wachter <dewachter.jonathan@gmail.com>, May 2018

from enum import IntEnum
import zmq
from yorokobi.agent import AGENT_ADDRESS

Request = IntEnum('Request', [
    'GET_STATUS',
    'RELOAD_CONFIGURATION',
    'BACKUP_NOW'
])

def do_request(request_type, timeout):
    context = zmq.Context.instance()
    socket = context.socket(zmq.REQ)

    socket.connect(AGENT_ADDRESS)
    socket.send_pyobj(request_type)

    if socket.poll(timeout) & zmq.POLLIN:
        response = socket.recv_pyobj()
    else:
        raise TimeoutError

    socket.disconnect(AGENT_ADDRESS)

    return response

def request_get_status(timeout):
    return do_request(Request.GET_STATUS, timeout)

def request_reload_configuration(timeout):
    return do_request(Request.RELOAD_CONFIGURATION, timeout)

def request_backup_now(timeout):
    return do_request(Request.BACKUP_NOW, timeout)
