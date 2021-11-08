import logging
import sys
from datetime import datetime

import pytz
from connect.client import ClientError, ConnectClient
from connect.reports.constants import REPORTS_ENV
from connect.reports.datamodels import Account, Report
from connect.reports.renderers import get_renderer

from executor.exception_handler import (
    handle_exception,
    handle_post_execution_exception,
    handle_preparation_exception,
)
from executor.utils import (
    get_default_reports_dir,
    get_report,
    get_report_definition,
    get_report_entrypoint,
    get_report_env,
    upload_file,
)


logger = logging.getLogger('executor')


def start():
    logger.info("Preparing environment for report execution")
    report_env = get_report_env()

    client = ConnectClient(
        endpoint=report_env['api_endpoint'],
        use_specs=False,
        api_key=report_env["client_token"],
        max_retries=3,
        default_limit=500,
    )

    try:
        report_to_execute = get_report(client, report_env["report_id"])
        logger.info(f"Preparing execution of report {report_to_execute}")
        report_definition = get_report_definition(report_to_execute['template']['entrypoint'])

    except (ClientError, Exception) as e:
        logger.exception('An error ocurred while preparing the execution environment.')
        handle_preparation_exception(e, client)

    result = execute_report(
        control_client=client,
        report_definition=report_definition,
        connect_report=report_to_execute,
    )

    if result:  # pragma: no branch
        try:
            upload_file(client, result, report_env["report_id"])
        except (ClientError, Exception) as e:
            logger.exception('An error ocurred during report upload.')
            handle_post_execution_exception(e, client)


def normalize_parameters(connect_parameters):
    parameters = {}
    for param in connect_parameters:
        parameters[param['id']] = param['value']

    return parameters


def execute_report(control_client, report_definition, connect_report):  # noqa: CCR001
    report_env = get_report_env()
    reports_dir = get_default_reports_dir()

    report_client = ConnectClient(
        endpoint=report_env["api_endpoint"],
        use_specs=False,
        api_key=report_env["client_token"],
        max_retries=3,
        default_limit=500,
    )
    connect_parameters = connect_report.get('parameters', [])
    parameters = normalize_parameters(connect_parameters)

    def progress(current_value, max_value):
        report = False
        if (
            max_value < 100 and current_value % 10 == 0
            or max_value < 1000 and current_value % 20 == 0
            or max_value < 10000 and current_value % 50 == 0
            or current_value % 2000 == 0
        ):
            report = True
        if report:  # pragma: no branch
            control_client.ns(
                'reporting',
            ).reports[report_env['report_id']].action(
                'progress',
            ).post(
                {
                    "progress": {
                        "max": max_value,
                        "value": current_value,
                    },
                },
            )

    if reports_dir not in sys.path:
        sys.path.append(reports_dir)
    try:
        report_entry_point = get_report_entrypoint(report_definition.entrypoint)
    except (ImportError, AttributeError) as e:
        logger.exception('An error ocurred while importing report entrypoint.')
        handle_preparation_exception(e, control_client)

    renderer_id = connect_report['renderer']
    renderer_definition = next(
        filter(
            lambda renderer: renderer.id == renderer_id, report_definition.renderers,
        ),
    )

    renderer = get_renderer(
        renderer_definition.type,
        REPORTS_ENV,
        reports_dir,
        Account(connect_report['owner']['id'], connect_report['owner']['name']),
        Report(
            report_definition.local_id,
            report_definition.name,
            report_definition.description,
            parameters,
        ),
        renderer_definition.template,
        renderer_definition.args,
    )

    try:
        args = [report_client, parameters, progress]
        if report_definition.report_spec == '2':
            args.extend(
                [
                    renderer_definition.type,
                    renderer.set_extra_context,
                ],
            )
        data = report_entry_point(*args)
        return renderer.render(data, '/report', start_time=datetime.now(tz=pytz.utc))
    except Exception as e:
        handle_exception(e, control_client, connect_report)


# Launch main process
if __name__ == '__main__':  # pragma: no cover
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(name)s %(levelname)s PID_%(process)d %(message)s',
    )
    try:  # pragma: no cover
        start()
    except BaseException:
        logger.critical('Unhandled exception has ocurred.', exc_info=True)
