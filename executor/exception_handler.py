from http import HTTPStatus

from connect.client import ClientError

from executor.utils import get_report, get_report_env


C_SUPPORT = '. Please contact support.'
UNAUTHORIZED = (401, 403)


def format_http_status(status_code):
    status = HTTPStatus(status_code)
    description = status.name.replace('_', ' ').title()
    return f'{status_code} - {description}'


def get_error_message_for_client(res: ClientError):
    status = format_http_status(res.status_code)

    if res.status_code in UNAUTHORIZED:
        return f'{status}: report tried to access objects not accessible by your account'

    if res.status_code == 400:
        code = res.error_code if res.error_code else 'Generic error'
        message = ','.join(res.errors) if res.errors else ''
        return f'{status}: {code} - {message}'
    return f'{status}: unexpected error: {res.message}'


def get_reason(e: Exception, report_type):
    if isinstance(e, ClientError):
        reason = get_error_message_for_client(e)
        if report_type != 'custom':
            reason = reason + C_SUPPORT
    else:
        reason = f'Report execution failed with error: {str(e)}'

    return reason


def report_to_be_blocked(e: Exception, report_type):
    if isinstance(e, RuntimeError):
        return False
    return True if report_type == 'custom' else False


def handle_exception(e: Exception, client, report=None):
    report_env = get_report_env()
    api_endpoint = report_env['api_endpoint']

    if not report:
        report = get_report(client, report_env['report_id'])

    block = report_to_be_blocked(e, report['template']['type'])
    reason = get_reason(e, report['template']['type'])

    if isinstance(e, ClientError):

        exception_cause = e.__cause__

        if exception_cause.request and exception_cause.request.url:  # pragma: no branch
            if e.status_code in UNAUTHORIZED and report['template']['type'] == 'custom':
                block = True
            else:
                # We will not block in the use case of exception caused by using any endpoint
                # More information at LITE-16960
                # to enable back, change the False to True on the else sentence
                block = False if exception_cause.request.url.startswith(api_endpoint) else False

        fail_report(
            client,
            report_env['report_id'],
            reason,
            block,
        )
        raise e
    fail_report(
        client,
        report_env['report_id'],
        reason,
        block,
    )
    raise e


def handle_preparation_exception(e: Exception, client):
    report_env = get_report_env()
    fail_report(
        client,
        report_env['report_id'],
        "An error happened while preparing report execution, please try again later or contact "
        "support",
        False,
    )

    raise e


def handle_post_execution_exception(e: Exception, client):
    report_env = get_report_env()
    report_id = report_env['report_id']
    fail_report(
        client,
        report_id,
        f'Error storing the report{C_SUPPORT}',
        False,
    )
    raise e


def fail_report(client, report_id, reason, block):
    return client.ns('reporting').reports[report_id].action('fail').post(
        {
            "notes": reason,
            "block": block,
        },
    )
