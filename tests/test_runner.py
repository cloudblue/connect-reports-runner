import logging

from connect.client import ClientError

from executor.runner import run_executor


def test_runner_exit_ok(mocker, mocked_env, caplog):
    process_poll = mocker.MagicMock(
        side_effect=[None, 0],
    )
    mocker.patch(
        'executor.runner.subprocess.Popen',
        return_value=mocker.MagicMock(poll=process_poll),
    )

    with caplog.at_level(logging.INFO):
        run_executor()

    assert caplog.records[1].message == 'Executor process has exited with 0.'


def test_runner_exit_ko_fail_ok(mocker, mocked_env, caplog):
    process_poll = mocker.MagicMock(
        side_effect=[None, 127],
    )
    mocker.patch(
        'executor.runner.subprocess.Popen',
        return_value=mocker.MagicMock(poll=process_poll),
    )

    fail_mock = mocker.patch('executor.runner.fail_report')

    with caplog.at_level(logging.INFO):
        run_executor()

    assert caplog.records[1].message == 'Executor process has exited with 127.'
    assert caplog.records[2].message.endswith('has been failed successfully.')
    fail_mock.assert_called_once()


def test_runner_exit_ko_fail_fail(mocker, mocked_env, caplog):
    process_poll = mocker.MagicMock(
        side_effect=[None, 127],
    )
    mocker.patch(
        'executor.runner.subprocess.Popen',
        return_value=mocker.MagicMock(poll=process_poll),
    )

    fail_mock = mocker.patch('executor.runner.fail_report', side_effect=ClientError('test error'))

    with caplog.at_level(logging.INFO):
        run_executor()

    assert caplog.records[1].message == 'Executor process has exited with 127.'
    assert caplog.records[2].message.endswith(' to fail status: test error')
    fail_mock.assert_called_once()
