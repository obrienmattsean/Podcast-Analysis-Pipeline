"""Unit tests for the connection_functions module.

Tests cover initialization of OpenAI, S3, and PostgreSQL clients with proper
error handling and validation of input parameters.
"""

from unittest.mock import MagicMock, patch

import pytest
from connection_functions import get_db_connection, get_llm_client, get_s3_client


class TestGetLlmClient:
    """Tests for get_llm_client function."""

    @patch("connection_functions.oa.OpenAI")
    def test_get_llm_client_success(self, mock_openai_class):
        """Test successful OpenAI client initialization with valid API key."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        result = get_llm_client("test-key-123")

        assert result == mock_client
        mock_openai_class.assert_called_once_with(api_key="test-key-123")

    def test_get_llm_client_empty_api_key(self):
        """Test that empty API key raises ValueError."""
        with pytest.raises(ValueError, match="API key cannot be empty"):
            get_llm_client("")

    def test_get_llm_client_missing_api_key(self):
        """Test that non-string API key raises TypeError."""
        with pytest.raises(TypeError, match="API key is required"):
            get_llm_client(None)

    @patch("connection_functions.oa.OpenAI")
    def test_get_llm_client_initialization_error(self, mock_openai_class):
        """Test that OpenAI initialization error is caught and re-raised."""
        mock_openai_class.side_effect = Exception("OpenAI API error")

        with pytest.raises(Exception, match="OpenAI API error"):
            get_llm_client("test-key-123")


class TestGetS3Client:
    """Tests for get_s3_client function."""

    @patch("connection_functions.boto3.client")
    def test_get_s3_client_success(self, mock_boto3_client):
        """Test successful S3 client initialization with valid credentials."""
        mock_s3 = MagicMock()
        mock_boto3_client.return_value = mock_s3

        result = get_s3_client(
            "AKIAIOSFODNN7EXAMPLE", "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY", "eu-west-2"
        )

        assert result == mock_s3
        mock_boto3_client.assert_called_once_with(
            "s3",
            aws_access_key_id="AKIAIOSFODNN7EXAMPLE",
            aws_secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            region_name="eu-west-2",
        )

    def test_get_s3_client_empty_access_key(self):
        """Test that empty access key raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            get_s3_client("", "secret-key", "eu-west-2")

    def test_get_s3_client_empty_secret_key(self):
        """Test that empty secret key raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            get_s3_client("access-key", "", "eu-west-2")

    def test_get_s3_client_empty_region(self):
        """Test that empty region raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            get_s3_client("access-key", "secret-key", "")

    def test_get_s3_client_non_string_access_key(self):
        """Test that non-string access key raises TypeError."""
        with pytest.raises(TypeError, match="are required"):
            get_s3_client(12345, "secret-key", "eu-west-2")

    def test_get_s3_client_non_string_secret_key(self):
        """Test that non-string secret key raises TypeError."""
        with pytest.raises(TypeError, match="are required"):
            get_s3_client("access-key", None, "eu-west-2")

    def test_get_s3_client_non_string_region(self):
        """Test that non-string region raises TypeError."""
        with pytest.raises(TypeError, match="are required"):
            get_s3_client("access-key", "secret-key", ["eu-west-2"])

    @patch("connection_functions.boto3.client")
    def test_get_s3_client_boto3_error(self, mock_boto3_client):
        """Test that boto3 client creation error is caught and re-raised."""
        mock_boto3_client.side_effect = Exception("boto3 connection failed")

        with pytest.raises(Exception, match="boto3 connection failed"):
            get_s3_client("access-key", "secret-key", "eu-west-2")


class TestGetDbConnection:
    """Tests for get_db_connection function."""

    @patch("connection_functions.connect")
    def test_get_db_connection_success(self, mock_connect):
        """Test successful database connection with valid parameters."""
        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection

        result = get_db_connection("localhost", "test_db", "test_user", "test_pass", "5432")

        assert result == mock_connection
        mock_connect.assert_called_once_with(
            host="localhost",
            port="5432",
            database="test_db",
            user="test_user",
            password="test_pass",
        )

    def test_get_db_connection_missing_host(self):
        """Test that empty host raises ValueError."""
        with pytest.raises(ValueError, match="missing in environment"):
            get_db_connection("", "test_db", "test_user", "test_pass", "5432")

    def test_get_db_connection_missing_port(self):
        """Test that empty port raises ValueError."""
        with pytest.raises(ValueError, match="missing in environment"):
            get_db_connection("localhost", "test_db", "test_user", "test_pass", "")

    def test_get_db_connection_non_string_host(self):
        """Test that non-string host raises TypeError."""
        with pytest.raises(TypeError, match="must be strings"):
            get_db_connection(12345, "test_db", "test_user", "test_pass", "5432")

    @patch("connection_functions.connect")
    def test_get_db_connection_psycopg2_error(self, mock_connect):
        """Test that psycopg2 connection error is caught and re-raised."""
        mock_connect.side_effect = Exception("Connection refused")

        with pytest.raises(Exception, match="Connection refused"):
            get_db_connection("localhost", "test_db", "test_user", "test_pass", "5432")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
