from unittest.mock import patch

from worker import cleanup_owned_computer


def test_preexisting_computer_is_never_deleted():
    computer_id = "cmp_aafb9b97334f"

    with patch("worker.delete_cloud_computer") as mock_delete:
        result = cleanup_owned_computer(
            computer_id=computer_id,
            owned_computer_id=None,
        )

    assert result["status"] == "skipped"
    mock_delete.assert_not_called()


def test_mismatched_computer_id_is_not_deleted():
    with patch("worker.delete_cloud_computer") as mock_delete:
        result = cleanup_owned_computer(
            computer_id="cmp-not-owned",
            owned_computer_id="cmp-created-by-this-run",
        )

    assert result["status"] == "skipped"
    mock_delete.assert_not_called()


def test_owned_computer_is_deleted():
    computer_id = "cmp-created-by-this-run"

    with patch("worker.delete_cloud_computer") as mock_delete:
        mock_delete.return_value = {"status": "deleted"}
        result = cleanup_owned_computer(
            computer_id=computer_id,
            owned_computer_id=computer_id,
        )

    assert result["status"] == "deleted"
    assert result["computer_id"] == computer_id
    mock_delete.assert_called_once_with(computer_id)


def test_cleanup_failure_is_reported():
    computer_id = "cmp-created-by-this-run"

    with patch("worker.delete_cloud_computer") as mock_delete:
        mock_delete.side_effect = RuntimeError("simulated delete failure")
        result = cleanup_owned_computer(
            computer_id=computer_id,
            owned_computer_id=computer_id,
        )

    assert result["status"] == "failed"
    assert "simulated delete failure" in result["reason"]
