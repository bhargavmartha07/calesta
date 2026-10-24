from unittest.mock import patch

from worker import run_in_celesto


def test_dangerous_command_is_blocked_before_celesto():
    computer_id = "cmp_aafb9b97334f"

    with patch("worker.celesto_cli") as mock_cli:
        result = run_in_celesto(computer_id, "rm -rf /")

    assert result["blocked_by_safety_hook"] is True
    assert result["exit_code"] == 126
    assert "Blocked command pattern" in result["stderr"]
    mock_cli.assert_not_called()


def test_safe_command_is_allowed_to_reach_cli():
    computer_id = "cmp_aafb9b97334f"

    with patch("worker.celesto_cli") as mock_cli:
        mock_cli.return_value = {
            "ok": True,
            "data": {
                "exit_code": 0,
                "stdout": "Safe diagnostic passed\n",
                "stderr": "",
            },
        }

        result = run_in_celesto(
            computer_id,
            "echo Safe diagnostic passed",
        )

    assert result["blocked_by_safety_hook"] is False
    mock_cli.assert_called_once()
