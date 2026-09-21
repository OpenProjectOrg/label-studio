import pytest
from core.utils.static_serve import serve, static_file_content_type_and_encoding
from django.http import Http404


class TestServeManifestFallback:
    def test_manifest_url_path_is_not_treated_as_absolute(self, tmp_path, monkeypatch, rf):
        """get_manifest_asset returns '/react-app/main.js' when HOST is empty."""
        monkeypatch.setattr('core.utils.static_serve.get_manifest_asset', lambda _path: '/react-app/main.js')
        request = rf.get('/react-app/main.js')

        with pytest.raises(Http404):
            serve(
                request,
                'main.js',
                document_root=str(tmp_path),
                manifest_asset_prefix='react-app',
            )

    def test_manifest_url_path_serves_file_inside_document_root(self, tmp_path, monkeypatch, rf):
        (tmp_path / 'main.js').write_text('ok')
        monkeypatch.setattr('core.utils.static_serve.get_manifest_asset', lambda _path: '/react-app/main.js')
        request = rf.get('/react-app/missing.js')

        response = serve(
            request,
            'missing.js',
            document_root=str(tmp_path),
            manifest_asset_prefix='react-app',
        )

        assert response.status_code == 200


class TestStaticFileContentType:
    def test_mjs_defaults_to_javascript_when_guess_type_unknown(self, monkeypatch):
        """Linux/Python builds may not map .mjs; PDF.js workers must not get octet-stream."""
        monkeypatch.setattr(
            'core.utils.static_serve.mimetypes.guess_type',
            lambda _path: (None, None),
        )

        content_type, encoding = static_file_content_type_and_encoding('/dist/pdf.worker-n-abc.mjs')

        assert content_type == 'text/javascript'
        assert encoding is None

    def test_known_extension_uses_mimetypes(self):
        content_type, encoding = static_file_content_type_and_encoding('/dist/main.js')

        assert content_type in {'text/javascript', 'application/javascript'}
        assert encoding is None

    def test_unknown_extension_falls_back_to_octet_stream(self, monkeypatch):
        monkeypatch.setattr(
            'core.utils.static_serve.mimetypes.guess_type',
            lambda _path: (None, None),
        )

        content_type, _encoding = static_file_content_type_and_encoding('/dist/data.bin')

        assert content_type == 'application/octet-stream'
