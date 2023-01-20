import json
import os
import platform
from importlib import import_module

from connect.reports.parser import parse
from connect.reports.validator import (
    validate,
    validate_with_schema,
)
from pkg_resources import DistributionNotFound, get_distribution

from executor.exceptions import RunnerException


def get_report(client, report_id):
    return client.ns('reporting').reports[report_id].get()


def get_report_id(func_fqn):
    tokens = func_fqn.split('.')
    if len(tokens) < 3:
        raise Exception("Reports project does not conform with specification")
    return tokens[1]


def get_report_entrypoint(func_fqn):
    module_name, func_name = func_fqn.rsplit('.', 1)
    module = import_module(module_name)
    return getattr(module, func_name)


def get_report_env():
    # Environment variables needed
    report_id = os.getenv('REPORT_ID', None)
    client_token = os.getenv('CLIENT_TOKEN', None)
    api_endpoint = os.getenv('API_ENDPOINT', None)

    required_vars = [
        report_id,
        client_token,
        api_endpoint,
    ]

    if None in required_vars:
        raise Exception("Wrong environment")

    return {
        "report_id": report_id,
        "client_token": client_token,
        "api_endpoint": api_endpoint,
    }


def get_default_reports_dir():
    if os.getenv('REPORTS_MOUNTPOINT'):
        return os.getenv('REPORTS_MOUNTPOINT')

    return os.path.join(
        '/',
        'reports',
        'reports',
    )


def load_descriptor_file(root_path: str):
    descriptor_file = os.path.join(root_path, 'reports.json')
    if not os.path.exists(descriptor_file):
        raise RunnerException('`reports.json` does not exist.')
    try:
        data = json.load(open(descriptor_file, 'r'))
        errors = validate_with_schema(data)
        if errors:
            raise RunnerException(f'Invalid `reports.json`: {errors}')
        repository_definition = parse(root_path, data)
        errors = validate(repository_definition)
        if errors:
            raise RunnerException(f'Invalid `reports.json`: {",".join(errors)}')
        return repository_definition
    except json.JSONDecodeError:
        raise RunnerException('`reports.json` is not a valid json file.')


def get_report_definition(entrypoint):
    root_path = get_default_reports_dir()
    repo_definition = load_descriptor_file(root_path)
    report = [reprt for reprt in repo_definition.reports if reprt.entrypoint == entrypoint][0]
    return report


def get_version():
    try:
        return get_distribution('connect-reports-runner').version
    except DistributionNotFound:
        return '0.0.0'


def get_user_agent():
    version = get_version()
    pimpl = platform.python_implementation()
    pver = platform.python_version()
    sysname = platform.system()
    sysver = platform.release()
    return {
        'User-Agent': (
            f'connect-reports-runner/{version} {pimpl}/{pver} {sysname}/{sysver}'
            f' {os.getenv("REPORT_ID", None)}'
        ),
    }


def upload_file(client, report_name, report_id, owner_id):
    report_filename = os.path.basename(report_name)
    reports_media_api = client.ns('media').ns('folders').collection('reports_report_file')
    media_file = reports_media_api[owner_id].action('files').post(
        data=open(report_name, 'rb'),
        headers={
            'Content-Type': 'application/octet-stream',
            'Content-Disposition': f'attachment; filename="{report_filename}"',
        },
    )

    return client.ns('reporting').reports[report_id].action('upload').post(
        payload={'file': {'id': json.loads(media_file)['id']}},
        headers=get_user_agent(),
    )
