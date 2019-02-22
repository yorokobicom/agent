import time
from pathlib import PurePosixPath, PosixPath
import signal
from multiprocessing import Process
import subprocess
from tempfile import TemporaryDirectory
import logging
from remofile import Server, generate_token
from yorokobi.configuration import get_default_configuration
from yorokobi.backup import Backup
import pytest

BACKUP_ID = "luqiPIMMS7MUVpVfyyS"
POSTGRESQL_PORT = 64383
POSTGRESQL_USER = "foobar"
POSTGRESQL_PASSWORD = "SbmkKXF9"
REMOFILE_PORT = 64384,
REMOFILE_TOKEN = generate_token()

def build_url(port, route):
    """ Utility function to build URL for unit tests. """

    # for instance, if port is 80 and route is '/hello-world', it creates
    # 'http://127.0.0.1:80/hello-world'
    return "http://127.0.0.1:{0}{1}".format(port, route)

@pytest.fixture
def postgresql():
    """ Fixture to start and stop a PostgreSQL server. """

    temporary_directory = TemporaryDirectory()

    # command = ['postgres']
    # command.extend(['-D', temporary_directory.name])
    command = ['ls']

    process = subprocess.Popen(command)

    yield

    process.terminate()
    process.wait()

    temporary_directory.cleanup()

@pytest.fixture
def remofile():
    """ Fixture to start and stop a Remofile server. """

    root_directory = TemporaryDirectory()
    root_directory_path = PosixPath(root_directory.name)

    def run_server(root_directory):
        server = Server(root_directory, REMOFILE_TOKEN)

        def handle_sigterm(signum, frame):
            handle_sigterm.server.terminate()

        handle_sigterm.server = server

        signal.signal(signal.SIGTERM, handle_sigterm)

        server.run(REMOFILE_PORT)

    process = Process(target=run_server, args=(root_directory_path,))
    process.start()

    time.sleep(0.05)

    yield root_directory, REMOFILE_PORT, REMOFILE_TOKEN

    process.terminate()
    process.join()

    root_directory.cleanup()

@pytest.fixture
def server():
    """ Fixture that starts and stops a web server.

    The web server simulates all the HTTP endpoints that is provided by
    the Yorkobi web server, including both all possible success and
    error responses.
    """

    app = Flask('yorokobi')

    @app.route('/v1/agents', methods=("POST",))
    def register_agent():

        assert request.authorization['username'] == LICENSE_KEY

        data = request.get_json()
        hostname   = data['hostname']
        ip_address = data['ip_address']

        assert hostname == socket.gethostname()
        assert ip_address == socket.gethostbyname(socket.gethostname())

        data = {
            "id"         : AGENT_ID,
            "hostname"   : hostname,
            "ip_address" : ip_address,
            "active"     : True
        }
        return jsonify(data), 200, {}

    @app.route('/v1/agents/<agent_id>', methods=("DELETE",))
    def unregister_agent(agent_id):

        assert agent_id == AGENT_ID

        assert request.authorization['username'] == LICENSE_KEY

        data = request.get_json()
        hostname   = data['hostname']
        ip_address = data['ip_address']

        assert hostname == socket.gethostname()
        assert ip_address == socket.gethostbyname(socket.gethostname())

        data = { # todo: add something here ?
        }
        return jsonify(data), 200, {}

    @app.route('/v1/backups', methods=("POST",))
    def perform_backup():

        assert request.authorization['username'] == LICENSE_KEY

        data = request.get_json()
        agent_id   = data['agent_id']
        hostname   = data['hostname']
        ip_address = data['ip_address']

        assert agent_id == AGENT_ID
        assert hostname == socket.gethostname()
        assert ip_address == socket.gethostbyname(socket.gethostname())

        data = { # todo: add something here ?
        }
        return jsonify(data), 200, {}

    @app.route('/cancel-backup', methods=("POST",))
    def cancel_backup():
        return 'ok'

    @app.route('/complete-backup', methods=("POST",))
    def complete_backup():
        return 'ok'

    app.config['TESTING'] = True
    # app.config['DEBUG'] = False
    app.config['DEBUG'] = True

    def run_application(app, port):
        app.run('127.0.0.1', port, threaded=False)

    application_args = app, PORT,
    process = Process(target=run_application, args=application_args)

    process.start()
    time.sleep(0.05) # give it some time to initialize

    yield

    process.terminate()
    process.join()

@pytest.fixture
def agent():

    # do something

    yield

    # do something


