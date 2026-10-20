"""Regression tests for the video recorder selectors.

Verifies that the selectors used in scripts/make_video.py actually exist
in the current demo/static/index.html, so the recorder won't time out.
"""

from pathlib import Path
import pytest

HTML_PATH = Path(__file__).resolve().parent.parent / "demo" / "static" / "index.html"
HTML = HTML_PATH.read_text(encoding="utf-8") if HTML_PATH.exists() else ""

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "make_video.py"
SCRIPT = SCRIPT_PATH.read_text(encoding="utf-8") if SCRIPT_PATH.exists() else ""


@pytest.mark.skipif(not HTML_PATH.exists(), reason="index.html not found")
class TestRecorderSelectorsInHTML:
    """All selectors used by make_video.py must exist in the current HTML."""

    def test_tutor_message_input_present(self):
        """#tutor-m must exist — this is the chat input the recorder types into."""
        assert 'id="tutor-m"' in HTML, (
            "Chat input #tutor-m not found. The recorder will fail with a timeout."
        )

    def test_tutor_img_input_present(self):
        """#tutor-img must exist — used for attaching images."""
        assert 'id="tutor-img"' in HTML, (
            "File input #tutor-img not found. Image attachment will fail."
        )

    def test_tutor_form_present(self):
        """#tutor-form must exist — the form the recorder submits."""
        assert 'id="tutor-form"' in HTML, (
            "Tutor form #tutor-form not found."
        )

    def test_tutor_nav_button_present(self):
        """data-page="tutor" nav button must exist — recorder clicks it to open AI Tutor."""
        assert 'data-page="tutor"' in HTML, (
            'Navigation button data-page="tutor" not found. Recorder cannot navigate to AI Tutor.'
        )

    def test_msg_bot_class_present(self):
        """.msg.bot class must exist — recorder waits for it after each response."""
        assert "msg bot" in HTML or "msg.bot" in HTML or ".msg.bot" in HTML, (
            "Bot message class not found. Recorder wait strategy may fail."
        )

    def test_old_selector_m_absent(self):
        """The OLD #m selector must NOT be present — confirms we're using the upgraded frontend."""
        # In the upgraded frontend the input is #tutor-m, not #m
        # #m existed only in the old kit example frontend
        old_m_as_id = 'id="m"' in HTML
        if old_m_as_id:
            pytest.fail(
                'Old selector id="m" found in HTML. This may cause the recorder to use the wrong input. '
                'The upgraded frontend uses id="tutor-m".'
            )

    def test_api_chat_in_html(self):
        """/api/chat must be in the frontend — recorder waits for this response."""
        assert "/api/chat" in HTML


@pytest.mark.skipif(not SCRIPT_PATH.exists(), reason="make_video.py not found")
class TestRecorderCodeSelectors:
    """make_video.py must use the correct selectors for the upgraded frontend."""

    def test_recorder_uses_tutor_m_not_m(self):
        """Recorder must use #tutor-m, not the old #m."""
        assert '"#tutor-m"' in SCRIPT or "'#tutor-m'" in SCRIPT, (
            'Recorder still uses old selector "#m". It must be updated to "#tutor-m".'
        )

    def test_recorder_not_uses_old_m(self):
        """Recorder must NOT use the old '#m' selector for fill/type."""
        # Check fill/type calls don't use the old #m
        import re
        old_uses = re.findall(r'(?:fill|type|press)\s*\(\s*["\']#m["\']', SCRIPT)
        assert not old_uses, f"Old #m selector still used in recorder: {old_uses}"

    def test_recorder_uses_tutor_img(self):
        """Recorder must use #tutor-img, not the old #img."""
        assert '"#tutor-img"' in SCRIPT or "'#tutor-img'" in SCRIPT, (
            'Recorder still uses old selector "#img". It must be updated to "#tutor-img".'
        )

    def test_recorder_not_uses_old_img(self):
        """Recorder must NOT use the old '#img' selector."""
        import re
        old_uses = re.findall(r'set_input_files\s*\(\s*["\']#img["\']', SCRIPT)
        assert not old_uses, f"Old #img selector still used in recorder: {old_uses}"

    def test_recorder_navigates_to_tutor(self):
        """Recorder must click the AI Tutor nav button before typing."""
        assert 'data-page="tutor"' in SCRIPT or "TUTOR_NAV" in SCRIPT, (
            "Recorder does not navigate to AI Tutor page. The chat input will not be visible."
        )

    def test_recorder_has_diagnostic_for_missing_input(self):
        """Recorder must raise a clear error if the input is not found."""
        assert "not found" in SCRIPT.lower() or "RuntimeError" in SCRIPT, (
            "Recorder has no diagnostic for missing input selector."
        )

    def test_recorder_not_uses_dataset_turns(self):
        """Recorder must NOT use document.body.dataset.turns — that no longer exists."""
        assert "dataset.turns" not in SCRIPT, (
            "Recorder still waits on document.body.dataset.turns which no longer exists in the upgraded frontend."
        )
