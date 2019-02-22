from yorokobi.cli import run_agent, setup_agent
from yorokobi.cli import register_agent, unregister_agent
from yorokobi.cli import backup_now
from yorokobi.cli import get_agent_status, get_agent_logs
from click.testing import CliRunner

def test_daemon_command():
    """ Test the command that runs the daemon. """

    runner = CliRunner(env=env)
    result = runner.invoke(run_agent, [])

    self.assertEqual(result.exit_code, default_exit_code)
    self.assertEqual(result.output, default_output)

def test_setup_command():
    """ Test the 'setup' command. """

    runner = CliRunner(env=env)
    result = runner.invoke(setup_agent, [])

    self.assertEqual(result.exit_code, default_exit_code)
    self.assertEqual(result.output, default_output)

def test_register_command():
    """ Test the 'register' command. """

    runner = CliRunner(env=env)
    result = runner.invoke(register_agent, [])

    self.assertEqual(result.exit_code, default_exit_code)
    self.assertEqual(result.output, default_output)

def test_unregister_command():
    """ Test the 'unregister' command. """


    runner = CliRunner(env=env)
    result = runner.invoke(unregister_agent, [])

    self.assertEqual(result.exit_code, default_exit_code)
    self.assertEqual(result.output, default_output)

def test_backup_command():
    """ Test the 'backup' command. """

    runner = CliRunner(env=env)
    result = runner.invoke(backup_now, [])

    self.assertEqual(result.exit_code, default_exit_code)
    self.assertEqual(result.output, default_output)

def test_status_command():
    """ Test the 'status' command. """

    runner = CliRunner(env=env)
    result = runner.invoke(get_agent_status, [])

    self.assertEqual(result.exit_code, default_exit_code)
    self.assertEqual(result.output, default_output)

def test_logs_command():
    """ Test the 'logs' command. """

    runner = CliRunner(env=env)
    result = runner.invoke(get_agent_logs, [])

    self.assertEqual(result.exit_code, default_exit_code)
    self.assertEqual(result.output, default_output)
