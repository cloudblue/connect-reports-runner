import json
import os
import tempfile

import pytest
from connect.client import ConnectClient
from pkg_resources import DistributionNotFound

from executor.exceptions import RunnerException
from executor.utils import (
    get_default_reports_dir,
    get_report,
    get_report_definition,
    get_report_entrypoint,
    get_report_env,
    get_report_id,
    get_user_agent,
    get_version,
    load_descriptor_file,
    upload_file,
)


def test_get_report_id():
    report_id = get_report_id('reports.fulfillment_requests.entrypoint.generate')
    assert report_id == 'fulfillment_requests'


def test_get_report_id_exception():
    with pytest.raises(Exception) as e:
        get_report_id('test')
    assert 'Reports project does' in str(e.value)


def test_load_reports():
    reports_dir = './tests/fixtures/reports/report_spec_v2'
    descriptor = load_descriptor_file(reports_dir)
    report = descriptor.reports[0]

    assert descriptor.name == 'Connect Reports Fixture'
    assert len(descriptor.reports) == 1
    assert report.entrypoint == 'super_report.entrypoint_v2.generate'


def test_get_report_definition(mocker):
    mocker.patch(
        'executor.utils.get_default_reports_dir',
        return_value='./tests/fixtures/reports/report_spec_v2',
    )
    report_definition = get_report_definition('super_report.entrypoint_v2.generate')
    assert report_definition.name == 'test report'
    assert report_definition.entrypoint == 'super_report.entrypoint_v2.generate'


def test_get_report_env_exception():
    os.environ.pop('API_ENDPOINT', None)
    with pytest.raises(Exception) as e:
        get_report_env()

    assert 'Wrong environment' in str(e.value)


def test_get_report_env(monkeypatch):
    monkeypatch.setenv("REPORT_ID", "report_id")
    monkeypatch.setenv("CLIENT_TOKEN", "client_token")
    monkeypatch.setenv("API_ENDPOINT", "api_endpoint")
    env = get_report_env()
    assert len(env) == 3
    assert env['report_id'] == 'report_id'
    assert env['client_token'] == 'client_token'
    assert env['api_endpoint'] == 'api_endpoint'


def test_get_report(mocked_responses, mocked_report_response_v1):
    client = ConnectClient(
        use_specs=False,
        api_key='ApiKey 123',
        endpoint='https://localhost/public/v1',
    )

    mocked_responses.add(
        method='GET',
        url='https://localhost/public/v1/reporting/reports/REC-000-000-0000-000000',
        json=mocked_report_response_v1,
    )

    response = get_report(client, 'REC-000-000-0000-000000')

    assert response == mocked_report_response_v1


def test_upload_file(mocked_responses, fs):

    client = ConnectClient(
        use_specs=False,
        api_key='ApiKey 123',
        endpoint='https://localhost/public/v1',
    )

    mocked_responses.add(
        method='POST',
        url='https://localhost/public/v1/media/folders/reports_report_file/VA-001/files',
        status=201,
        body=b'{"id": "MFL-001"}',
    )

    mocked_responses.add(
        method='POST',
        url='https://localhost/public/v1/reporting/reports/REC-000-000-0000-000000/upload',
        status=204,
        json={},
    )
    import os
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        import pathlib
        zipfile = os.path.join(tmpdir, 'report.zip')
        pathlib.Path(zipfile).touch()
        response = upload_file(client, zipfile, 'REC-000-000-0000-000000', 'VA-001')

    assert response is None


def test_load_descriptor_file_no_file():
    reports_dir = './tests/fixtures/reports'
    with pytest.raises(RunnerException) as error:
        load_descriptor_file(reports_dir)
    assert str(error.value) == '`reports.json` does not exist.'


def test_load_descriptor_invalid_json_file(mocker):
    with tempfile.TemporaryDirectory() as tmp_data:
        os.mkdir(f'{tmp_data}/project_dir')
        with open(f'{tmp_data}/project_dir/reports.json', 'w') as fp:
            fp.write('foo')

        with pytest.raises(RunnerException) as error:
            load_descriptor_file(f'{tmp_data}/project_dir')

        assert str(error.value) == '`reports.json` is not a valid json file.'


def test_load_descriptor_validation_schema_fail(mocker, mocked_reports_json_v2):
    mocked_reports_json_v2.pop('name')

    with tempfile.TemporaryDirectory() as tmp_data:
        os.mkdir(f'{tmp_data}/project_dir')
        with open(f'{tmp_data}/project_dir/reports.json', 'w') as fp:
            json.dump(mocked_reports_json_v2, fp)

        with pytest.raises(RunnerException) as error:
            load_descriptor_file(f'{tmp_data}/project_dir')

        assert 'Invalid `reports.json`' in str(error.value)


def test_load_descriptor_repo_validation_fail(mocker, mocked_reports_json_v2):
    with tempfile.TemporaryDirectory() as tmp_data:
        os.mkdir(f'{tmp_data}/project_dir')
        with open(f'{tmp_data}/project_dir/reports.json', 'w') as fp:
            json.dump(mocked_reports_json_v2, fp)

        with pytest.raises(RunnerException) as error:
            load_descriptor_file(f'{tmp_data}/project_dir')

        assert 'Invalid `reports.json`' in str(error.value)


@pytest.mark.parametrize(
    ('set_env'),
    ('custom_path', ''),
)
def test_get_default_reports_dir(set_env):
    os.environ['REPORTS_MOUNTPOINT'] = set_env
    result = get_default_reports_dir()
    if set_env:
        assert result == set_env
    else:
        assert result == '/reports/reports'


def test_get_report_entrypoint():
    result = get_report_entrypoint('os.path.join')

    assert type(result).__name__ == 'function'
    assert result('a', 'b') == 'a/b'


def test_get_version(mocker):
    mocked = mocker.MagicMock()
    mocked.version = '22.0'
    mocker.patch(
        'executor.utils.get_distribution',
        return_value=mocked,
    )
    assert get_version() == '22.0'


def test_get_version_exception(mocker):
    mocker.patch(
        'executor.utils.get_distribution',
        side_effect=DistributionNotFound(),
    )
    assert get_version() == '0.0.0'


def test_get_user_agent(mocker):
    mocker.patch('executor.utils.platform.python_implementation', return_value='1')
    mocker.patch('executor.utils.platform.python_version', return_value='3.15')
    mocker.patch('executor.utils.platform.system', return_value='Linux')
    mocker.patch('executor.utils.platform.release', return_value='1.0')
    mocker.patch('executor.utils.get_version', return_value='22.0')
    expected_ua = 'connect-reports-runner/22.0 1/3.15 Linux/1.0 REC-000-000-0000-000000'
    os.environ['REPORT_ID'] = 'REC-000-000-0000-000000'
    assert get_user_agent() == {'User-Agent': expected_ua}
