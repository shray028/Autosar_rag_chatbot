"""
Static UI regression tests for the browser chat client.

The UI is a single HTML file, so these tests assert the JavaScript contains
the behaviors needed for the issues reported from the screenshot.
"""

from pathlib import Path


HTML = (Path(__file__).resolve().parents[1] / "static" / "index.html").read_text(
    encoding="utf-8"
)


class TestChatUiRegressions:
    """Protect core chat UX behavior."""

    def test_health_poll_uses_cached_status_endpoint(self):
        assert "fetch(`${API_BASE}/health/status`)" in HTML
        assert "setInterval(checkHealth, 30000)" in HTML

    def test_send_clears_inputs_immediately(self):
        send_message_body = HTML.split("async function sendMessage(text) {", 1)[1].split(
            "// ─── Add Messages", 1
        )[0]
        assert "const submittedText = text.trim();" in send_message_body
        assert "welcomeInput.value = '';" in send_message_body
        assert "chatInput.value = '';" in send_message_body
        assert "addMessage(submittedText, 'user');" in send_message_body

    def test_ui_disables_slow_llm_reranking_for_chat(self):
        assert "skip_reranking: true" in HTML

    def test_api_errors_are_formatted_before_display(self):
        assert "function formatApiError(payload)" in HTML
        assert "Array.isArray(detail)" in HTML
        assert "JSON.stringify(detail)" in HTML
        assert "formatApiError(data)" in HTML
