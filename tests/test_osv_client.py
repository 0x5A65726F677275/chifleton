"""Tests for OSV client."""

import pytest
from unittest.mock import patch, Mock
from scanner.osv_client import query_vulnerabilities, get_vulns_from_response


def test_get_vulns_from_response_empty() -> None:
    assert get_vulns_from_response({}) == []
    assert get_vulns_from_response({"vulns": []}) == []


def test_get_vulns_from_response_list() -> None:
    vulns = [{"id": "OSV-1", "summary": "Test"}]
    assert get_vulns_from_response({"vulns": vulns}) == vulns


def test_get_vulns_from_response_error() -> None:
    assert get_vulns_from_response({"_error": "timeout", "vulns": []}) == []


@patch("scanner.osv_client.requests.post")
def test_query_vulnerabilities_success(mock_post: Mock) -> None:
    mock_post.return_value = Mock(
        status_code=200,
        json=lambda: {"vulns": [{"id": "GHSA-xxx"}]},
        raise_for_status=Mock(),
    )
    result = query_vulnerabilities("requests", "2.28.0")
    assert result.get("vulns") == [{"id": "GHSA-xxx"}]
    call = mock_post.call_args
    assert call[1]["json"]["package"]["name"] == "requests"
    assert call[1]["json"]["package"]["ecosystem"] == "PyPI"
    assert call[1]["json"]["version"] == "2.28.0"


@patch("scanner.osv_client.requests.post")
def test_query_vulnerabilities_no_version(mock_post: Mock) -> None:
    mock_post.return_value = Mock(
        status_code=200,
        json=lambda: {"vulns": []},
        raise_for_status=Mock(),
    )
    result = query_vulnerabilities("flask", None)
    assert "vulns" in result
    payload = mock_post.call_args[1]["json"]
    assert "version" not in payload
    assert payload["package"]["name"] == "flask"
