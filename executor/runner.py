import logging
import subprocess

from connect.client import ClientError, ConnectClient

from executor.exception_handler import fail_report
from executor.utils import get_report_env, get_user_agent


logger = logging.getLogger('runner')


def run_executor():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(name)s %(levelname)s PID_%(process)d %(message)s',
    )

    report_env = get_report_env()
    report_id = report_env['report_id']

    proc = subprocess.Popen(
        [
            'python',
            '-m',
            'executor.executor',
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    logger.info(f'Executor started: PID {proc.pid}, report: {report_id}')
    stdout, stderr = proc.communicate()

    if proc.returncode == 0:
        logger.info('Executor process has exited with 0.')
        return

    logger.error(f'Executor process has exited with {proc.returncode}: {stdout=} {stderr=}.')

    client = ConnectClient(
        endpoint=report_env['api_endpoint'],
        use_specs=False,
        api_key=report_env['client_token'],
        max_retries=3,
        default_headers=get_user_agent(),
    )
    try:
        fail_report(
            client,
            report_id,
            'Report execution has failed due contains too much data, please try to exclude '
            'using report parameters some of it and try again.',
            False,
        )
        logger.info(f'Report {report_id} has been failed successfully.')
    except ClientError as ce:
        logger.warning(f'Cannot switch report {report_id} to fail status: {ce}')
    return


if __name__ == '__main__':  # pragma: no cover
    run_executor()
