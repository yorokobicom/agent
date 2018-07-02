# Copyright (C) LIVE INTERACTIVE SA - All Rights Reserved
# Yorokobi Agent - Automatic database backups for web applications
#
# The source code is proprietary and confidential. Unauthorized copying
# of this file, via any medium, is strictly prohibited.
#
# Written by Jonathan De Wachter <dewachter.jonathan@gmail.com>, May 2018

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
            # FIXME: use hostname and port
            connection = psycopg2.connect(dbname='postgres', user=username, password=password)
            is_connected_to_postgresql = True
        except:
            print("Unable to connect to the PostgreSQL server for some reasons") # TODO: DETERMINE WHY
            
        if not is_connected_to_postgresql:                    
            retry = input("Retry? [Y/n]")
            
            if retry != 'y' and retry != 'Y':
                return []

    selected_dbs = select_databases(connection)
    connection.close()
    
    config['postgresql-user']     = username
    config['postgresql-password'] = password
    config['postgresql-host']     = host
    config['postgresql-port']     = port
    
    config['selected-dbs'] = selected_dbs

def select_databases(connection):

    cursor = connection.cursor()
    cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")

    foo = cursor.fetchall()
    var = tuple(bar[0] for bar in foo)

    print(var)

    # print("Move with UP and DOWN keywords.")
    # print("Press SPACE to select and uncheck and ENTER to continue.")


    choices = ('All databases', *var)
    print(choices)


    import os
    import sys
    import re
    sys.path.append(os.path.realpath('.'))
    from pprint import pprint

    import inquirer

    questions = [
        inquirer.Checkbox('databases',
                      message="What size do you need?",
                      choices=choices,
                  ),
    ]

    answers = inquirer.prompt(questions)

    pprint(answers)
