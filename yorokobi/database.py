import inquirer
import psycopg2

def configure_databases(config):
    """ Configure database workflow.

    Enter the PostgreSQL database selection workflow.

        PostgreSQL Username:
        PostgreSQL Password:

        Optional. Leave blank if you are unsure.
        PostgreSQL Host [localhost]:

        Optional. Leave blank if you are unsure.
        PostgreSQL Port [5432]:
    """

    is_connected_to_postgresql = False

    while not is_connected_to_postgresql:
        username = input("PostgreSQL Username: ")
        password = input("PostgreSQL Password: ")

        print("Optional. Leave blank if you are unsure.")
        host = input("PostgreSQL Host [localhost]:")

        print("Optional. Leave blank if you are unsure.")
        port = input("PostgreSQL Port [5432]:")

        if host == '':
            host = 'localhost'

        if port == '':
            port = 5432
        else:
            port = int(port)

        try:
            connection = psycopg2.connect(dbname='postgres', user=username, password=password, host=host, port=str(port))
            is_connected_to_postgresql = True
        except:
            print("Unable to connect to the PostgreSQL server for some reasons.")

        if not is_connected_to_postgresql:
            retry = input("Retry? [Y/n]")

            if retry != 'y' and retry != 'Y':
                return []

    databases = get_databases(connection)
    selected_dbs = select_databases(databases)
    connection.close()

    config['postgresql-user']     = username
    config['postgresql-password'] = password
    config['postgresql-host']     = host
    config['postgresql-port']     = port

    config['selected-dbs'] = selected_dbs

def get_databases(connection):
    cursor = connection.cursor()
    cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")

    response = cursor.fetchall()
    return tuple(row[0] for row in response)

def select_databases(databases):
    """ Brief description.

    Long description.
    """

    print("Move with UP and DOWN keywords.")
    print("Press SPACE to select and uncheck and ENTER to continue.", end='\n\n')

    choices = ('All databases', *databases)

    questions = [
        inquirer.Checkbox('databases',
                      message="Select the databases you want to backup",
                      choices=choices,
                  ),
    ]

    answers = inquirer.prompt(questions)

    # if the list is empty, returns None, if the list contains
    # 'All databases', return 'all', or return the actual list of
    # selected DBs
    if not answers['databases']:
        return None
    elif 'All databases' in answers['databases']:
        return 'all'
    else:
        return answers['databases']
