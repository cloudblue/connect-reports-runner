import os
import sys
from unittest.mock import MagicMock

import pytest
from connect.client import ClientError, ConnectClient
from connect.reports.constants import DEFAULT_RENDERER_ID
from connect.reports.datamodels import (
    RendererDefinition,
    ReportDefinition,
)

import executor.executor


def test_execute_report_v1(
    mocker,
    mocked_env,
    mocked_responses,
    mocked_dir_v1,
    report_v1_json,
    mocked_report_response_v1_fake_fs,
):
    root_path = os.getenv('REPORTS_MOUNTPOINT')

    report_json = report_v1_json(
        entrypoint='basic_report.entrypoint_v1.generate',
        template='basic_report/template.xlsx')
    template = report_json.pop('template')
    start_row = report_json.pop('start_row')
    start_col = report_json.pop('start_col')

    renderer = RendererDefinition(
        root_path=root_path,
        id=DEFAULT_RENDERER_ID,
        type='xlsx',
        description='Render report to Excel.',
        default=True,
        template=template,
        args={
            'start_row': start_row,
            'start_col': start_col,
        },
    )
    report_definition = ReportDefinition(
        root_path=root_path,
        renderers=[renderer],
        **report_json)

    mocker.patch(
        'executor.executor.get_report_definition',
        return_value=report_definition,
    )

    mocked_responses.add(
        method='GET',
        url='https://localhost/public/v1/reporting/reports/REC-000-000-0000-000000',
        json=mocked_report_response_v1_fake_fs,
    )
    mocked_responses.add(
        method='POST',
        url='https://localhost/public/v1/reporting/reports/REC-000-000-0000-000000/progress',
        status=204,
        json={},
    )
    mocked_responses.add(
        method='POST',
        url='https://localhost/public/v1/media/folders/reports_report_file/VA-000-000/files',
        status=201,
        body=b'{"id": "MFL-001"}',
    )
    mocked_responses.add(
        method='POST',
        url='https://localhost/public/v1/reporting/reports/REC-000-000-0000-000000/upload',
        status=204,
        json={},
    )

    executor.executor.start()


def test_execute_report_v2(
    mocker,
    mocked_env,
    mocked_responses,
    mocked_dir_v2,
    report_v2_json,
    mocked_report_response_v2_fake_fs,
):
    root_path = os.getenv('REPORTS_MOUNTPOINT')
    xlsx_renderer = RendererDefinition(
        root_path=root_path,
        id='xlsx_renderer',
        type='xlsx',
        description='Excel renderer.',
        default=True,
        template='super_report/template.xlsx',
        args={
            'start_row': 1,
            'start_col': 1,
        },
    )
    report_json = report_v2_json(
        name='pending fulfillment requests',
        readme_file='Readme.md',
        entrypoint='super_report.entrypoint_v2.generate',
        renderers=[xlsx_renderer],
    )
    report_definition = ReportDefinition(
        root_path=root_path,
        **report_json,
    )
    mocker.patch(
        'executor.executor.get_report_definition',
        return_value=report_definition,
    )

    mocked_report_response_v2_fake_fs['renderer'] = 'xlsx_renderer'
    mocked_report_response_v2_fake_fs['entrypoint'] = report_definition.entrypoint

    mocked_responses.add(
        method='GET',
        url='https://localhost/public/v1/reporting/reports/REC-000-000-0000-000000',
        json=mocked_report_response_v2_fake_fs,
    )
    mocked_responses.add(
        method='POST',
        url='https://localhost/public/v1/reporting/reports/REC-000-000-0000-000000/progress',
        status=204,
        json={},
    )
    mocked_responses.add(
        method='POST',
        url='https://localhost/public/v1/media/folders/reports_report_file/VA-000-000/files',
        status=201,
        body=b'{"id": "MFL-001"}',
    )
    mocked_responses.add(
        method='POST',
        url='https://localhost/public/v1/reporting/reports/REC-000-000-0000-000000/upload',
        status=204,
        json={},
    )

    executor.executor.start()


@pytest.mark.parametrize(
    'entrypoint',
    (
        'entrypoint_v2_async',
        'entrypoint_v2_async_gen',
    ),
)
def test_execute_report_v2_async(
    mocker,
    mocked_env,
    mocked_responses,
    mocked_dir_v2,
    report_v2_json,
    mocked_report_response_v2_fake_fs,
    entrypoint,
):
    root_path = os.getenv('REPORTS_MOUNTPOINT')
    xlsx_renderer = RendererDefinition(
        root_path=root_path,
        id='xlsx_renderer',
        type='xlsx',
        description='Excel renderer.',
        default=True,
        template='super_report/template.xlsx',
        args={
            'start_row': 1,
            'start_col': 1,
        },
    )
    report_json = report_v2_json(
        name='pending fulfillment requests',
        readme_file='Readme.md',
        entrypoint=f'super_report.{entrypoint}.generate',
        renderers=[xlsx_renderer],
    )
    report_definition = ReportDefinition(
        root_path=root_path,
        **report_json,
    )
    mocker.patch(
        'executor.executor.get_report_definition',
        return_value=report_definition,
    )

    mocked_report_response_v2_fake_fs['renderer'] = 'xlsx_renderer'
    mocked_report_response_v2_fake_fs['entrypoint'] = report_definition.entrypoint

    mocked_responses.add(
        method='GET',
        url='https://localhost/public/v1/reporting/reports/REC-000-000-0000-000000',
        json=mocked_report_response_v2_fake_fs,
    )
    mocked_responses.add(
        method='POST',
        url='https://localhost/public/v1/reporting/reports/REC-000-000-0000-000000/progress',
        status=204,
        json={},
    )
    mocked_responses.add(
        method='POST',
        url='https://localhost/public/v1/media/folders/reports_report_file/VA-000-000/files',
        status=201,
        body=b'{"id": "MFL-001"}',
    )
    mocked_responses.add(
        method='POST',
        url='https://localhost/public/v1/reporting/reports/REC-000-000-0000-000000/upload',
        status=204,
        json={},
    )

    executor.executor.start()


def test_execute_report_error_on_report_code_controlled(
    mocker,
    mocked_env,
    mocked_responses,
    mocked_report_response_v2_fake_fs,
    report_v2_json,
    param_json,
    mocked_dir_v2,
):
    root_path = mocked_dir_v2
    sys.path.append(root_path)
    xlsx_renderer = RendererDefinition(
        root_path=root_path,
        id='xlsx_renderer',
        type='xlsx',
        description='Excel renderer.',
        default=True,
        template='super_report/template.xlsx',
        args={
            'start_row': 1,
            'start_col': 1,
        },
    )
    json_renderer = RendererDefinition(
        root_path=root_path,
        id='json_renderer',
        type='json',
        description='Json renderer.',
        default=False,
    )
    report_json = report_v2_json(
        name='pending fulfillment requests',
        readme_file='Readme.md',
        entrypoint='super_report.entrypoint_v2.generate',
        parameters=[param_json()],
        renderers=[xlsx_renderer, json_renderer],
    )

    report_definition = ReportDefinition(
        root_path=root_path,
        **report_json,
    )
    mocker.patch(
        'executor.executor.get_report_definition',
        return_value=report_definition,
    )

    mocked_report_response_v2_fake_fs['renderer'] = 'xlsx_renderer'

    mocked_responses.add(
        method='GET',
        url='https://localhost/public/v1/reporting/reports/REC-000-000-0000-000000',
        json=mocked_report_response_v2_fake_fs,
    )

    mocker.patch(
        'super_report.entrypoint_v2.generate',
        side_effect=RuntimeError("Custom error"),
    )
    upload = mocker.patch(
        'executor.exception_handler.fail_report',
    )
    client = ConnectClient(
        use_specs=False,
        api_key=os.getenv('CLIENT_TOKEN'),
        endpoint=os.getenv('API_ENDPOINT'),
    )
    mocker.patch(
        'executor.executor.ConnectClient',
        return_value=client,
    )

    with pytest.raises(RuntimeError) as e:
        executor.executor.start()

    assert isinstance(e.value, RuntimeError)
    upload.assert_called_with(
        client,
        'REC-000-000-0000-000000',
        'Report execution failed with error: Custom error',
        False,
    )


def test_execute_report_upload_error(
    mocker,
    mocked_env,
    mocked_responses,
    mocked_dir_v2,
    report_v2_json,
    mocked_report_response_v2_fake_fs,
):
    root_path = os.getenv('REPORTS_MOUNTPOINT')
    xlsx_renderer = RendererDefinition(
        root_path=root_path,
        id='xlsx_renderer',
        type='xlsx',
        description='Excel renderer.',
        default=True,
        template='super_report/template.xlsx',
        args={
            'start_row': 1,
            'start_col': 1,
        },
    )
    report_json = report_v2_json(
        name='pending fulfillment requests',
        readme_file='Readme.md',
        entrypoint='super_report.entrypoint_v2.generate',
        renderers=[xlsx_renderer],
    )
    report_definition = ReportDefinition(
        root_path=root_path,
        **report_json,
    )
    mocker.patch(
        'executor.executor.get_report_definition',
        return_value=report_definition,
    )

    mocked_report_response_v2_fake_fs['renderer'] = 'xlsx_renderer'
    mocked_report_response_v2_fake_fs['entrypoint'] = report_definition.entrypoint

    mocked_responses.add(
        method='GET',
        url='https://localhost/public/v1/reporting/reports/REC-000-000-0000-000000',
        json=mocked_report_response_v2_fake_fs,
    )
    mocked_responses.add(
        method='POST',
        url='https://localhost/public/v1/reporting/reports/REC-000-000-0000-000000/progress',
        status=204,
        json={},
    )
    mocked_responses.add(
        method='POST',
        url='https://localhost/public/v1/media/folders/reports_report_file/VA-000-000/files',
        status=500,
        body=b'{"id": "MFL-001"}',
    )

    with pytest.raises(ClientError) as e:
        executor.executor.start()

    assert isinstance(e.value, ClientError)


def test_execute_error_exception_import_module(
    mocker,
    mocked_env,
    mocked_responses,
    mocked_dir_v2,
    report_v2_json,
    mocked_report_response_v2_fake_fs,
):
    root_path = os.getenv('REPORTS_MOUNTPOINT')
    xlsx_renderer = RendererDefinition(
        root_path=root_path,
        id='xlsx_renderer',
        type='xlsx',
        description='Excel renderer.',
        default=True,
        template='super_report/template.xlsx',
        args={
            'start_row': 1,
            'start_col': 1,
        },
    )
    report_json = report_v2_json(
        name='pending fulfillment requests',
        readme_file='Readme.md',
        entrypoint='super_report.entrypoint_v2.generate',
        renderers=[xlsx_renderer],
    )
    report_definition = ReportDefinition(
        root_path=root_path,
        **report_json,
    )

    mocker.patch(
        'executor.executor.get_report_definition',
        return_value=report_definition,
    )

    mocked_responses.add(
        method='GET',
        url='https://localhost/public/v1/reporting/reports/REC-000-000-0000-000000',
        json=mocked_report_response_v2_fake_fs,
    )
    mocked_responses.add(
        method='POST',
        url='https://localhost/public/v1/reporting/reports/REC-000-000-0000-000000/fail',
        json={},
    )
    mocker.patch(
        'executor.executor.get_report_entrypoint',
        side_effect=ImportError("Some import error"),
    )
    with pytest.raises(ImportError) as e:
        executor.executor.start()

    assert isinstance(e.value, ImportError)


def test_execute_error_prepration(
    mocked_env,
    mocker,
):
    mocker.patch(
        'executor.executor.get_report',
        side_effect=ClientError(MagicMock()),
    )

    with pytest.raises(Exception) as e:
        executor.executor.start()

    assert isinstance(e.value, ClientError)


def test_execute_report_error_on_report_code(
    mocker,
    mocked_env,
    mocked_responses,
    mocked_dir_v2,
    mocked_report_response_v2_fake_fs,
    report_v2_json,
):
    root_path = os.getenv('REPORTS_MOUNTPOINT')

    xlsx_renderer = RendererDefinition(
        root_path=root_path,
        id='xlsx_renderer',
        type='xlsx',
        description='Excel renderer.',
        default=True,
        template='super_report/template.xlsx',
        args={
            'start_row': 1,
            'start_col': 1,
        },
    )
    json_renderer = RendererDefinition(
        root_path=root_path,
        id='json_renderer',
        type='json',
        description='Json renderer.',
        default=False,
    )
    report_json = report_v2_json(
        name='pending fulfillment requests',
        readme_file='Readme.md',
        entrypoint='super_report.entrypoint_v2.generate',
        renderers=[xlsx_renderer, json_renderer],
    )

    report_definition = ReportDefinition(
        root_path=root_path,
        **report_json,
    )
    mocker.patch(
        'executor.executor.get_report_definition',
        return_value=report_definition,
    )

    mocked_report_response_v2_fake_fs['renderer'] = 'xlsx_renderer'
    mocked_report_response_v2_fake_fs['entrypoint'] = report_definition.entrypoint

    mocked_responses.add(
        method='GET',
        url='https://localhost/public/v1/reporting/reports/REC-000-000-0000-000000',
        json=mocked_report_response_v2_fake_fs,
    )
    mocked_responses.add(
        method='POST',
        url='https://localhost/public/v1/reporting/reports/REC-000-000-0000-000000/fail',
        json={},
    )
    sys.path.append(
        os.path.join(os.path.dirname(__file__), 'fixtures', 'reports', 'report_spec_v2'))
    mocker.patch(
        'super_report.entrypoint_v2.generate',
        side_effect=ValueError("Whatever"),
    )

    with pytest.raises(ValueError) as e:
        executor.executor.start()

    assert isinstance(e.value, ValueError)
