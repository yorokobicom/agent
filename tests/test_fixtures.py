
from fixtures import server, build_url

def test_fixture(server):

    # test register the agent endpoint
    url = build_url(PORT, '/v1/agents')

    auth = HTTPBasicAuth(LICENSE_KEY, '')
    data = {
        'hostname'  : socket.gethostname(),
        'ip_address': socket.gethostbyname(socket.gethostname())
    }

    response = requests.post(url, json=data, auth=auth)

    # test perform a backup endpoint
    url = build_url(PORT, '/v1/backups')

    auth = HTTPBasicAuth(LICENSE_KEY, '')
    data = {
        'agent_id'  : AGENT_ID,
        'hostname'  : socket.gethostname(),
        'ip_address': socket.gethostbyname(socket.gethostname())
    }

    response = requests.post(url, json=data, auth=auth)

    # test cancel a backup endpoint
    pass

    # test complete a backup endpoint
    pass

    # test unregister the agent endpoint
    url = build_url(PORT, '/v1/agents/{0}'.format(AGENT_ID))

    auth = HTTPBasicAuth(LICENSE_KEY, '')
    data = {
        'hostname'  : socket.gethostname(),
        'ip_address': socket.gethostbyname(socket.gethostname())
    }

    response = requests.delete(url, json=data, auth=auth)
