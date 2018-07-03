# Yorokobi Protocols

The Yorokobi agent uses two protocols. One is Python object oriented used by the front-end CLI to communicate with the agent running in the background. And the other one is JSON oriented and is used by the agent to communicate with the back-up server.

*The communiation between the front-end CLI and the agent is Python objects because they're both, and will remain, writen in Python. However, the back-up server might be written in a different language and this is why keeping a language agnostic format was chosen.*

## Front-end CLI to agent

The front-end CLI sends **requests** to the agent and sends back **responses** using Python directories seriazlied with the the `pickle` module. It's all hidden by the bindings Python of `ZeroMQ`. Directories always contain a `type` field, and additional fields related to the request or response.

There are 4 types of request.

* GET_STATUS
* RELOAD_CONFIGURATION
* BACKUP-NOW

3 requests = ('get-status', 'reload-configuration', 'backup-now')

->
GET_STATUS
<-
foobar



->
RELOAD_CONFIGURATION
<-
ACCEPTED, config
REFUSED, "error message"


->
BACKUP_NOW
<-
ACCEPTED, backup-id
REFUSED, "ongoing backup"

## Agent to back-up server

The agent sends **requests** to the back-up server and sends back **responses** using a very simple JSON format that all starts with a `type` field indicating the type of request or response, then it's followed by fields related to the request or response.

There are 4 types of request.

* register-license
* initiate-backup
* cancel-backup
* terminate-backup

There are 2 types of response.

* accepted
* refused

Unlike requests, responses always have one, and only one, additional field which is `reason`.

Example of JSON request and response.

```
{
  'type' : 'register-license',
  'foo'  : 'bar'
}
```

```
{
  'type' : 'accepted',
  'foo'  : 'bar'
}
```

### Register a license

Request `register-license` is a stand-alone request to identify an agent. The agent sends a license key (previously purchased by a customer) and the back-up server replies with an agent ID if it's accepted.


Example of request.

```
{
  'type' : 'register-license',
  'foo'  : 'bar'
}
```

### Do a back-up cycle

Request `initiate-backup`, `cancel-backup` and `terminate-backup` form a cycle to sends back-up over to the server. The `initiate-backup` 
request will .

Requests:

* REGISTER_LICENSE
* INITIATE_BACKUP
* TERMINATE_BACKUP
* CANCEL_BACKUP


->
REGISTER_LICENSE, license_key

<-
ACCEPTED, agent_id
REFUSED, reason


->
INITIATE_BACKUP, agent_id, license_key

<-
ACCEPTED, backup_id, port, token
REFUSED, reason



->
TERMINATE_BACKUP, agent_id, license_key

<-
ACCEPTED, backup_id, port, token
REFUSED, reason


->
CANCEL_BACKUP

<-
ACCEPTED, ok
REFUSED, foo, bar

