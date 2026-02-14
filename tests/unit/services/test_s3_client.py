"""Unit tests for S3 client snapshot operations."""

from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.unit


class TestUploadSnapshot:
    @patch("src.atm.services.s3_client.settings")
    def test_upload_success(self, mock_settings: MagicMock) -> None:
        """upload_snapshot puts JSON to S3 on success."""
        mock_settings.s3_bucket_name = "my-bucket"
        mock_settings.aws_region = "us-east-1"

        mock_client = MagicMock()
        with patch("src.atm.services.s3_client._get_s3_client", return_value=mock_client):
            from src.atm.services.s3_client import upload_snapshot

            result = upload_snapshot({"version": "1.0"}, "test.json")

        assert result is True
        mock_client.put_object.assert_called_once()
        call_kwargs = mock_client.put_object.call_args.kwargs
        assert call_kwargs["Bucket"] == "my-bucket"
        assert call_kwargs["Key"] == "snapshots/test.json"
        assert '"version": "1.0"' in call_kwargs["Body"]

    @patch("src.atm.services.s3_client._get_s3_client", return_value=None)
    def test_upload_no_client(self, _mock: MagicMock) -> None:
        """upload_snapshot returns False when _get_s3_client returns None."""
        from src.atm.services.s3_client import upload_snapshot

        result = upload_snapshot({"version": "1.0"}, "test.json")
        assert result is False


class TestDownloadSnapshot:
    @patch("src.atm.services.s3_client.settings")
    def test_download_success(self, mock_settings: MagicMock) -> None:
        """download_snapshot returns parsed JSON from S3."""
        mock_settings.s3_bucket_name = "my-bucket"
        mock_settings.aws_region = "us-east-1"

        body_mock = MagicMock()
        body_mock.read.return_value = b'{"version": "1.0", "customers": []}'
        mock_client = MagicMock()
        mock_client.get_object.return_value = {"Body": body_mock}

        with patch("src.atm.services.s3_client._get_s3_client", return_value=mock_client):
            from src.atm.services.s3_client import download_snapshot

            result = download_snapshot("snapshots/test.json")

        assert result is not None
        assert result["version"] == "1.0"
        mock_client.get_object.assert_called_once_with(
            Bucket="my-bucket", Key="snapshots/test.json"
        )

    @patch("src.atm.services.s3_client._get_s3_client", return_value=None)
    def test_download_no_client(self, _mock: MagicMock) -> None:
        """download_snapshot returns None when _get_s3_client returns None."""
        from src.atm.services.s3_client import download_snapshot

        result = download_snapshot("snapshots/test.json")
        assert result is None


class TestListSnapshots:
    @patch("src.atm.services.s3_client.settings")
    def test_list_success(self, mock_settings: MagicMock) -> None:
        """list_snapshots returns keys from S3."""
        mock_settings.s3_bucket_name = "my-bucket"
        mock_settings.aws_region = "us-east-1"

        mock_client = MagicMock()
        mock_client.list_objects_v2.return_value = {
            "Contents": [
                {"Key": "snapshots/a.json"},
                {"Key": "snapshots/b.json"},
            ]
        }

        with patch("src.atm.services.s3_client._get_s3_client", return_value=mock_client):
            from src.atm.services.s3_client import list_snapshots

            result = list_snapshots()

        assert result == ["snapshots/a.json", "snapshots/b.json"]

    @patch("src.atm.services.s3_client.settings")
    def test_list_empty(self, mock_settings: MagicMock) -> None:
        """list_snapshots returns empty list when no objects exist."""
        mock_settings.s3_bucket_name = "my-bucket"
        mock_settings.aws_region = "us-east-1"

        mock_client = MagicMock()
        mock_client.list_objects_v2.return_value = {}

        with patch("src.atm.services.s3_client._get_s3_client", return_value=mock_client):
            from src.atm.services.s3_client import list_snapshots

            result = list_snapshots()

        assert result == []

    @patch("src.atm.services.s3_client._get_s3_client", return_value=None)
    def test_list_no_client(self, _mock: MagicMock) -> None:
        """list_snapshots returns empty list when _get_s3_client returns None."""
        from src.atm.services.s3_client import list_snapshots

        result = list_snapshots()
        assert result == []


class TestGetS3Client:
    @patch("src.atm.services.s3_client.settings")
    def test_no_bucket_configured(self, mock_settings: MagicMock) -> None:
        """_get_s3_client returns None when s3_bucket_name is empty."""
        mock_settings.s3_bucket_name = ""
        from src.atm.services.s3_client import _get_s3_client

        result = _get_s3_client()
        assert result is None

    @patch("src.atm.services.s3_client.settings")
    def test_boto3_import_error(self, mock_settings: MagicMock) -> None:
        """_get_s3_client returns None when boto3 import fails."""
        mock_settings.s3_bucket_name = "my-bucket"
        mock_settings.aws_region = "us-east-1"

        import builtins

        original_import = builtins.__import__

        def mock_import(name: str, *args: object, **kwargs: object) -> object:
            if name == "boto3":
                raise ImportError("No module named 'boto3'")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            from src.atm.services.s3_client import _get_s3_client

            result = _get_s3_client()

        assert result is None
