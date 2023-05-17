import logging

from connect.client import ClientError

from executor.runner import run_executor


def test_runner_exit_ok(mocker, mocked_env, caplog):
    communicate_mock = mocker.MagicMock(
        return_value=(
            bytes('stdout', 'utf-8'),
            bytes('some stack trace', 'utf-8'),
        ),
    )
    mocker.patch(
        'executor.runner.subprocess.Popen',
        return_value=mocker.MagicMock(
            communicate=communicate_mock,
            returncode=0,
        ),
    )

    with caplog.at_level(logging.INFO):
        run_executor()

    assert caplog.records[1].message == 'Executor process has exited with 0.'


def test_runner_exit_ko_fail_ok(mocker, mocked_env, caplog):
    communicate_mock = mocker.MagicMock(
        return_value=(
            bytes('stdout', 'utf-8'),
            bytes('some stack trace', 'utf-8'),
        ),
    )
    mocker.patch(
        'executor.runner.subprocess.Popen',
        return_value=mocker.MagicMock(
            communicate=communicate_mock,
            returncode=127,
        ),
    )

    fail_mock = mocker.patch('executor.runner.fail_report')

    with caplog.at_level(logging.INFO):
        run_executor()

    assert caplog.records[1].message == (
        "Executor process has exited with 127: stdout=b'stdout' stderr=b'some stack trace'."
    )
    assert caplog.records[2].message.endswith('has been failed successfully.')
    fail_mock.assert_called_once()
    assert fail_mock.call_args[0][4] == 'stdout: stdout stderr: some stack trace'


def test_runner_exit_ko_fail_fail(mocker, mocked_env, caplog):
    communicate_mock = mocker.MagicMock(
        return_value=(
            bytes('stdout', 'utf-8'),
            bytes('stderr', 'utf-8'),
        ),
    )
    mocker.patch(
        'executor.runner.subprocess.Popen',
        return_value=mocker.MagicMock(
            communicate=communicate_mock,
            returncode=127,
        ),
    )

    fail_mock = mocker.patch('executor.runner.fail_report', side_effect=ClientError('test error'))

    with caplog.at_level(logging.INFO):
        run_executor()

    assert caplog.records[1].message == (
        "Executor process has exited with 127: stdout=b'stdout' stderr=b'stderr'."
    )
    assert caplog.records[2].message.endswith(' to fail status: test error')
    fail_mock.assert_called_once()
