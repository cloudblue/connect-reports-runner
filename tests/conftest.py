import json
import os
import sys

import pytest
import responses


@pytest.fixture(scope='function')
def mocked_responses():
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture(scope='function')
def mocked_env():
    os.environ["REPORT_ID"] = "REC-000-000-0000-000000"
    os.environ["CLIENT_TOKEN"] = "ApiKey 123"
    os.environ["API_ENDPOINT"] = "https://localhost/public/v1"


# REPORT SPEC V1

@pytest.fixture(scope='function')
def mocked_report_response_v1():
    with open('./tests/fixtures/report_response_v1.json') as response:
        return json.load(response)


@pytest.fixture(scope='function')
def mocked_report_response_v1_fake_fs(fs):
    real_file = os.path.join(
        sys.path[0],
        'tests/fixtures/report_response_v1.json',
    )
    fs.add_real_file(real_file)
    with open(real_file) as response:
        return json.load(response)


@pytest.fixture(scope='function')
def mocked_dir_v1(fs):
    # as exposed by https://docs.python.org/3/library/sys.html
    # path[0] contains always where script was initiated

    real_dir = os.path.join(
        sys.path[0],
        'tests/fixtures/reports/report_spec_v1',
    )
    fs.add_real_directory(
        source_path=real_dir,
        target_path='/reports/reports',
    )
    fs.add_real_directory(real_dir)
    os.environ['REPORTS_MOUNTPOINT'] = real_dir


@pytest.fixture(scope='function')
def param_json():
    def _param_data(
        id='updated', type='date_range',
        name='param name', description='param description',
        required=True, choices=None,
    ):
        data = {
            'id': id,
            'type': type,
            'name': name,
            'description': description,
            'required': required,
        }
        if choices is not None:
            data['choices'] = choices

        return data

    return _param_data


@pytest.fixture(scope='function')
def report_v1_json(param_json):
    def _report_data(
        name='Report',
        readme_file='Readme.md',
        entrypoint='module.entrypoint.generate',
        audience=['vendor', 'provider'],  # noqa: B006
        parameters=[param_json()],  # noqa: B006
        template='module/template.xlsx',
        start_row=1,
        start_col=1,
    ):

        data = {
            'name': name,
            'readme_file': readme_file,
            'entrypoint': entrypoint,
            'audience': audience,
            'parameters': parameters,
            'report_spec': '1',
            'template': template,
            'start_row': start_row,
            'start_col': start_col,
        }
        return data

    return _report_data


# REPORT SPEC V2

@pytest.fixture(scope='function')
def mocked_report_response_v2_fake_fs(fs):
    real_file = os.path.join(
        sys.path[0],
        'tests/fixtures/report_response_v2.json',
    )
    fs.add_real_file(real_file)
    with open(real_file) as response:
        return json.load(response)


@pytest.fixture(scope='function')
def mocked_dir_v2(fs):
    real_dir = os.path.join(
        sys.path[0],
        'tests/fixtures/reports/report_spec_v2',
    )
    fs.add_real_directory(
        source_path=real_dir,
        target_path='/reports/reports',
    )
    fs.add_real_directory(real_dir)
    os.environ['REPORTS_MOUNTPOINT'] = real_dir
    return real_dir


@pytest.fixture(scope='function')
def mocked_reports_json_v2():
    with open('./tests/fixtures/reports/report_spec_v2/reports.json') as response:
        return json.load(response)


@pytest.fixture(scope='function')
def report_v2_json(param_json):
    def _report_data(
        name='report name',
        readme_file='Readme.md',
        entrypoint='module.entrypoint.generate',
        audience=['vendor', 'provider'],  # noqa: B006
        parameters=[param_json()],  # noqa: B006
        renderers=[],  # noqa: B006
    ):
        data = {
            'name': name,
            'readme_file': readme_file,
            'entrypoint': entrypoint,
            'audience': audience,
            'parameters': parameters,
            'renderers': renderers,
            'report_spec': '2',
        }
        return data

    return _report_data
