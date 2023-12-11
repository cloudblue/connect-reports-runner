import os

import pytest
from connect.client import ClientError, ConnectClient
from requests import Request, RequestException

from executor.exception_handler import (
    handle_exception,
    handle_post_execution_exception,
    handle_preparation_exception,
)


def test_post_execution_error(
        mocked_env,
        mocked_responses,
):
    client = ConnectClient(
        use_specs=False,
        api_key=os.getenv('CLIENT_TOKEN'),
        endpoint=os.getenv('API_ENDPOINT'),
    )
    mocked_responses.add(
        method='POST',
        url='https://localhost/public/v1/reporting/reports/REC-000-000-0000-000000/fail',
        json={},
    )
    exception = ClientError(
        message="weird error uploading",
        status_code=500,
        error_code=500,
    )

    with pytest.raises(ClientError) as e:
        handle_post_execution_exception(exception, client)

    assert 'weird error uploading' in str(e.value)


def test_handle_preparation_exception_getting_report(
    mocked_env,
    mocked_responses,
):
    client = ConnectClient(
        use_specs=False,
        api_key=os.getenv('CLIENT_TOKEN'),
        endpoint=os.getenv('API_ENDPOINT'),
    )
    mocked_responses.add(
        method='POST',
        url='https://localhost/public/v1/reporting/reports/REC-000-000-0000-000000/fail',
        json={},
    )
    exception = ClientError(
        message="weird error uploading",
        status_code=500,
        error_code=500,
    )

    with pytest.raises(ClientError) as e:
        handle_preparation_exception(exception, client)

    assert 'weird error uploading' in str(e.value)


@pytest.mark.parametrize("ex_type", [ValueError, AttributeError, ImportError, ModuleNotFoundError])
def test_handle_report_execution_different_errors(
    mocker,
    mocked_env,
    mocked_responses,
    mocked_report_response_v1,
    ex_type,
):
    client = ConnectClient(
        use_specs=False,
        api_key=os.getenv('CLIENT_TOKEN'),
        endpoint=os.getenv('API_ENDPOINT'),
    )
    mocked_responses.add(
        method='GET',
        url='https://localhost/public/v1/reporting/reports/REC-000-000-0000-000000',
        json=mocked_report_response_v1,
    )
    exception = ex_type("Some Value Error")

    upload = mocker.patch(
        'executor.exception_handler.fail_report',
    )
    with pytest.raises(ex_type) as e:
        handle_exception(exception, client)

    assert isinstance(e.value, ex_type)
    upload.assert_called_with(
        client,
        'REC-000-000-0000-000000',
        'Report execution failed with error: Some Value Error',
        True,
    )


def test_handle_report_execution_row_limit_errors(
    mocker,
    mocked_env,
    mocked_responses,
    mocked_report_response_v1,
):
    client = ConnectClient(
        use_specs=False,
        api_key=os.getenv('CLIENT_TOKEN'),
        endpoint=os.getenv('API_ENDPOINT'),
    )
    mocked_responses.add(
        method='GET',
        url='https://localhost/public/v1/reporting/reports/REC-000-000-0000-000000',
        json=mocked_report_response_v1,
    )
    exception = ValueError(
        'Row numbers must be between 1 and 1048576. Row number supplied was 1048577',
    )

    upload = mocker.patch(
        'executor.exception_handler.fail_report',
    )
    with pytest.raises(ValueError):
        handle_exception(exception, client)

    upload.assert_called_with(
        client,
        'REC-000-000-0000-000000',
        'Report execution failed with error: Row numbers must be between '
        '1 and 1048576. Row number supplied was 1048577',
        False,
    )


def test_handle_report_execution_409_outside_connect_block(
    mocker,
    mocked_env,
    mocked_responses,
    mocked_report_response_v1,
):
    mocked_report_response_v1['template']['type'] = 'custom'
    client = ConnectClient(
        use_specs=False,
        api_key=os.getenv('CLIENT_TOKEN'),
        endpoint=os.getenv('API_ENDPOINT'),
    )
    mocked_responses.add(
        method='GET',
        url='https://localhost/public/v1/reporting/reports/REC-000-000-0000-000000',
        json=mocked_report_response_v1,
    )
    exception = ClientError(
        status_code=409,
        error_code=409,
        message="Test",
        errors=[
            "error 1",
            "error 2",
        ],
    )

    request_exception = RequestException(
        request=Request(
            method='GET',
            url='https://www.google.com',
        ),
    )
    exception.__cause__ = request_exception

    upload = mocker.patch(
        'executor.exception_handler.fail_report',
    )

    with pytest.raises(ClientError):
        handle_exception(exception, client)

    # Change False to True in case that firewall reenabled as per LITE-16960
    upload.assert_called_with(
        client,
        'REC-000-000-0000-000000',
        '409 - Conflict: unexpected error: Test',
        False,
    )


def test_handle_report_execution_409_connect_no_block(
    mocker,
    mocked_env,
    mocked_responses,
    mocked_report_response_v1,
):
    mocked_report_response_v1['template']['type'] = 'custom'
    client = ConnectClient(
        use_specs=False,
        api_key=os.getenv('CLIENT_TOKEN'),
        endpoint=os.getenv('API_ENDPOINT'),
    )
    mocked_responses.add(
        method='GET',
        url='https://localhost/public/v1/reporting/reports/REC-000-000-0000-000000',
        json=mocked_report_response_v1,
    )
    exception = ClientError(
        status_code=409,
        error_code=409,
        message="Test",
        errors=[
            "error 1",
            "error 2",
        ],
    )

    request_exception = RequestException(
        request=Request(
            method='GET',
            url='https://localhost/public/v1',
        ),
    )
    exception.__cause__ = request_exception

    upload = mocker.patch(
        'executor.exception_handler.fail_report',
    )

    with pytest.raises(ClientError):
        handle_exception(exception, client)

    upload.assert_called_with(
        client,
        'REC-000-000-0000-000000',
        '409 - Conflict: unexpected error: Test',
        False,
    )


@pytest.mark.parametrize("report_type", ["custom", "system"])
def test_handle_report_execution_500_connect_no_block(
    mocker,
    mocked_env,
    mocked_responses,
    mocked_report_response_v1,
    report_type,
):
    mocked_report_response_v1['template']['type'] = report_type
    client = ConnectClient(
        use_specs=False,
        api_key=os.getenv('CLIENT_TOKEN'),
        endpoint=os.getenv('API_ENDPOINT'),
    )
    mocked_responses.add(
        method='GET',
        url='https://localhost/public/v1/reporting/reports/REC-000-000-0000-000000',
        json=mocked_report_response_v1,
    )
    exception = ClientError(
        status_code=500,
        error_code=500,
        message="Internal error",
        errors=[
            "error 1",
            "error 2",
        ],
    )

    request_exception = RequestException(
        request=Request(
            method='GET',
            url='https://localhost/public/v1',
        ),
    )
    exception.__cause__ = request_exception

    upload = mocker.patch(
        'executor.exception_handler.fail_report',
    )

    with pytest.raises(ClientError):
        handle_exception(exception, client)
    error = "500 - Internal Server Error: unexpected error: Internal error"
    if report_type == 'system':
        error = error + ". Please contact support."
    upload.assert_called_with(
        client,
        'REC-000-000-0000-000000',
        error,
        False,
    )


@pytest.mark.parametrize("report_type", ["custom", "system"])
def test_handle_report_execution_500(
    mocker,
    mocked_env,
    mocked_responses,
    mocked_report_response_v1,
    report_type,
):
    mocked_report_response_v1['template']['type'] = report_type
    client = ConnectClient(
        use_specs=False,
        api_key=os.getenv('CLIENT_TOKEN'),
        endpoint=os.getenv('API_ENDPOINT'),
    )
    mocked_responses.add(
        method='GET',
        url='https://localhost/public/v1/reporting/reports/REC-000-000-0000-000000',
        json=mocked_report_response_v1,
    )
    exception = ClientError(
        status_code=500,
        error_code=500,
        message="Internal error",
        errors=[
            "error 1",
            "error 2",
        ],
    )

    request_exception = RequestException(
        request=Request(
            method='GET',
            url='https://localhost/public/v1',
        ),
    )
    exception.__cause__ = request_exception

    upload = mocker.patch(
        'executor.exception_handler.fail_report',
    )

    with pytest.raises(ClientError):
        handle_exception(exception, client)
    error = "500 - Internal Server Error: unexpected error: Internal error"
    if report_type == 'system':
        error = error + ". Please contact support."
    upload.assert_called_with(
        client,
        'REC-000-000-0000-000000',
        error,
        False,
    )


@pytest.mark.parametrize("report_type", ["custom", "system"])
def test_handle_report_execution_401(
    mocker,
    mocked_env,
    mocked_responses,
    mocked_report_response_v1,
    report_type,
):
    mocked_report_response_v1['template']['type'] = report_type
    client = ConnectClient(
        use_specs=False,
        api_key=os.getenv('CLIENT_TOKEN'),
        endpoint=os.getenv('API_ENDPOINT'),
    )
    mocked_responses.add(
        method='GET',
        url='https://localhost/public/v1/reporting/reports/REC-000-000-0000-000000',
        json=mocked_report_response_v1,
    )
    exception = ClientError(
        status_code=401,
        error_code=401,
        message="Internal error",
        errors=[
            "error 1",
            "error 2",
        ],
    )

    request_exception = RequestException(
        request=Request(
            method='GET',
            url='https://localhost/public/v1',
        ),
    )
    exception.__cause__ = request_exception

    upload = mocker.patch(
        'executor.exception_handler.fail_report',
    )

    with pytest.raises(ClientError):
        handle_exception(exception, client)
    error = "401 - Unauthorized: report tried to access objects not accessible by your account"
    if report_type == 'system':
        error = error + ". Please contact support."

    block = True if report_type == 'custom' else False
    upload.assert_called_with(
        client,
        'REC-000-000-0000-000000',
        error,
        block,
    )


@pytest.mark.parametrize("report_type", ["custom", "system"])
def test_handle_report_execution_400(
    mocker,
    mocked_env,
    mocked_responses,
    mocked_report_response_v1,
    report_type,
):
    mocked_report_response_v1['template']['type'] = report_type
    client = ConnectClient(
        use_specs=False,
        api_key=os.getenv('CLIENT_TOKEN'),
        endpoint=os.getenv('API_ENDPOINT'),
    )
    mocked_responses.add(
        method='GET',
        url='https://localhost/public/v1/reporting/reports/REC-000-000-0000-000000',
        json=mocked_report_response_v1,
    )
    exception = ClientError(
        status_code=400,
        error_code=400,
        message="Internal error",
        errors=[
            "error 1",
            "error 2",
        ],
    )

    request_exception = RequestException(
        request=Request(
            method='GET',
            url='https://localhost/public/v1',
        ),
    )
    exception.__cause__ = request_exception

    upload = mocker.patch(
        'executor.exception_handler.fail_report',
    )

    with pytest.raises(ClientError):
        handle_exception(exception, client)
    error = "400 - Bad Request: 400 - error 1,error 2"
    if report_type == 'system':
        error = error + ". Please contact support."

    upload.assert_called_with(
        client,
        'REC-000-000-0000-000000',
        error,
        False,
    )
