import time
from pathlib import PurePosixPath, PosixPath
import signal
from multiprocessing import Process
import subprocess
from tempfile import TemporaryDirectory
import logging
import pexpect
from remofile import Server, generate_token
import docker
from yorokobi.configuration import get_default_configuration
from yorokobi.backup import Backup
import pytest

LICENSE_KEY = "M8ddTKx_87Iw2_EPvR9FD8Ol8_MGrqEe0LaGorsAh9Q"
AGENT_ID = "uLPtJZvx4UD0R_lfKf"
BACKUP_ID = "luqiPIMMS7MUVpVfyyS"

POSTGRESQL_PORT = 64383
POSTGRESQL_PASSWORD = "SbmkKXF9"

REMOFILE_PORT = 64384,
REMOFILE_TOKEN = generate_token()

def build_url(port, route):
    """ Utility function to build URL for unit tests. """

    # for instance, if port is 80 and route is '/hello-world', it creates
    # 'http://127.0.0.1:80/hello-world'
    return "http://127.0.0.1:{0}{1}".format(port, route)

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
def postgresql():
    """ Fixture to start and stop a PostgreSQL server.

    The fixtures starts a Docker container using the `postgres:11` image
    in the Docker Hub. After that, it imports the Shakespeare database
    using the 'psql' command.

    It's somewhat equivalent to the following commands.

        sudo docker run -d --name {name} -e POSTGRES_PASSWORD={password} -p {port}:5432 postgres:11
        psql --host=127.0.0.1 --port={port} --username=postgres --password --file=shakespeare.sql

        sudo docker stop -t 0 db
        sudo docker rm db

    Long description.
    """

    # start a Docker container using the 'postgres:11' image
    client = docker.from_env()

    images = client.images.pull('postgres:11')
    container = client.containers.run('postgres:11',
        environment = [f"POSTGRES_PASSWORD={POSTGRESQL_PASSWORD}"],
        ports       = {'5432/tcp' : POSTGRESQL_PORT},
        detach      = True)

    # import the shakespeare database
    command = f"psql --host=127.0.0.1 --port={POSTGRESQL_PORT} --username=postgres --password --file=shakespeare.sql"

    child = pexpect.spawn(command, timeout=None)
    child.expect('Password')
    child.sendline(POSTGRESQL_PASSWORD)

    # send username, password and port to unit tests
    yield "postgres", POSTGRESQL_PASSWORD, POSTGRESQL_PORT

    # stop and remove the Docker container
    container.stop(timeout=0)
    container.remove()

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
def agent():

    # do something

    yield

    # do something


