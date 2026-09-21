from unittest.mock import patch

import pytest
from django.test import override_settings
from io_storages.s3.utils import S3StorageError, catch_and_reraise_from_none, get_client_and_resource


@override_settings(S3_TRUSTED_STORAGE_DOMAINS=['trusted-domain.com'])
def test_catch_and_reraise_from_none_with_untrusted_domain():
    class TestClass:
        s3_endpoint = 'http://untrusted-domain.com'

    instance = TestClass()

    @catch_and_reraise_from_none
    def function_to_test(self):
        raise Exception('Original Exception')

    with patch('io_storages.s3.utils.extractor.extract_urllib') as mock_extract:
        mock_extract.return_value.registered_domain = 'untrusted-domain.com'
        with pytest.raises(S3StorageError) as excinfo:
            function_to_test(instance)
        assert 'Debugging info is not available for s3 endpoints on domain: untrusted-domain.com' in str(excinfo.value)


@override_settings(S3_TRUSTED_STORAGE_DOMAINS=['trusted-domain.com'])
def test_catch_and_reraise_from_none_with_trusted_domain():
    class TestClass:
        s3_endpoint = 'http://trusted-domain.com'

    instance = TestClass()

    @catch_and_reraise_from_none
    def function_to_test(self):
        raise Exception('Original Exception')

    with patch('io_storages.s3.utils.extractor.extract_urllib') as mock_extract:
        mock_extract.return_value.registered_domain = 'trusted-domain.com'
        with pytest.raises(Exception) as excinfo:
            function_to_test(instance)
        assert 'Original Exception' in str(excinfo.value)


@override_settings(S3_TRUSTED_STORAGE_DOMAINS=['rustfs'])
def test_catch_and_reraise_from_none_with_single_label_host():
    class TestClass:
        s3_endpoint = 'http://rustfs:9000'

    instance = TestClass()

    @catch_and_reraise_from_none
    def function_to_test(self):
        raise Exception('Original Exception')

    with patch('io_storages.s3.utils.extractor.extract_urllib') as mock_extract:
        mock_extract.return_value.registered_domain = ''
        mock_extract.return_value.domain = 'rustfs'
        with pytest.raises(Exception) as excinfo:
            function_to_test(instance)
        assert 'Original Exception' in str(excinfo.value)


@patch('io_storages.s3.utils.boto3.Session')
def test_custom_endpoint_uses_path_addressing(session_cls):
    session = session_cls.return_value
    get_client_and_resource(
        aws_access_key_id='k',
        aws_secret_access_key='s',
        s3_endpoint='http://rustfs:9000',
    )
    kwargs = session.client.call_args.kwargs
    assert kwargs['endpoint_url'] == 'http://rustfs:9000'
    assert kwargs['config'].s3['addressing_style'] == 'path'


@patch('io_storages.s3.utils.boto3.Session')
def test_aws_default_does_not_force_path_style(session_cls):
    session = session_cls.return_value
    get_client_and_resource(aws_access_key_id='k', aws_secret_access_key='s')
    kwargs = session.client.call_args.kwargs
    assert 'endpoint_url' not in kwargs
    assert not getattr(kwargs['config'], 's3', None) or kwargs['config'].s3.get('addressing_style') != 'path'
