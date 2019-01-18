from setuptools import setup
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='yorokobi',
    version='0.1.0',
    packages=[
        'yorokobi'
    ],
    description='Automatic database backups for web applications',
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=[
        'psycopg2-binary',
        'click',
        'pyzmq',
        'schedule',
        'inquirer',
        'requests',
        'remofile',
        'pexpect'
    ],
    dependency_links=['https://github.com/yorokobicom/remofile/tarball/master#egg=remofile']
    entry_points='''
        [console_scripts]
        yorokobid=yorokobi.cli:run_agent
        yorokobi=yorokobi.cli:cli
    ''',
    test_suite="tests"
)
