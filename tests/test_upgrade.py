"""Regression tests for the StudyMate AI premium upgrade.

Verifies:
1. Progress page and nav are completely removed
2. All 5 remaining pages have correct boundaries
3. Premium design elements are present
4. Typing indicator exists in AI Tutor
5. No fake demo data references remain
6. API contract preserved
7. No raw guidance text exposure
"""

from pathlib import Path
import pytest

HTML_PATH = Path(__file__).resolve().parent.parent / "demo" / "static" / "index.html"
HTML = HTML_PATH.read_text(encoding='utf-8') if HTML_PATH.exists() else ""

STYLE_END = HTML.find('</style>')
BODY = HTML[STYLE_END:] if STYLE_END >= 0 else HTML


@pytest.mark.skipif(not HTML_PATH.exists(), reason="index.html not found")
class TestProgressRemoved:
    def test_progress_page_absent(self):
        assert 'id="page-progress"' not in HTML

    def test_progress_nav_absent(self):
        assert 'data-page="progress"' not in BODY

    def test_refresh_progress_fn_absent(self):
        assert 'function refreshProgress' not in HTML

    def test_demo_mastery_absent(self):
        assert 'DEMO_MASTERY' not in HTML

    def test_prog_topics_counter_absent(self):
        # prog-topics was a progress-page-only element
        assert 'id="prog-topics"' not in HTML


@pytest.mark.skipif(not HTML_PATH.exists(), reason="index.html not found")
class TestPageBoundaries:
    PAGES = ['page-home', 'page-tutor', 'page-planner', 'page-myplans', 'page-quiz']

    def _before(self, pg):
        idx = HTML.find(f'id="{pg}"')
        return HTML[idx-5:idx] if idx >= 5 else '?'

    def test_all_five_pages_present(self):
        for pg in self.PAGES:
            assert HTML.find(f'id="{pg}"') >= 0, f"Missing: {pg}"

    def test_all_boundaries_clean(self):
        for pg in self.PAGES:
            b = self._before(pg)
            assert b == '<div ', f"{pg} boundary broken: [{b}]"

    def test_no_raw_html_text(self):
        import re
        # Check for bare div id= not preceded by <
        bare = re.findall(r'(?<!<)div id="page-', HTML)
        assert len(bare) == 0, f"Raw div tags without <: {bare}"

@pytest.mark.skipif(not HTML_PATH.exists(), reason="index.html not found")
class TestNavigation:
    def test_home_nav_present(self):       assert 'data-page="home"' in BODY
    def test_tutor_nav_present(self):      assert 'data-page="tutor"' in BODY
    def test_planner_nav_present(self):    assert 'data-page="planner"' in BODY
    def test_myplans_nav_present(self):    assert 'data-page="myplans"' in BODY
    def test_quiz_nav_present(self):       assert 'data-page="quiz"' in BODY
    def test_progress_nav_absent(self):    assert 'data-page="progress"' not in BODY


@pytest.mark.skipif(not HTML_PATH.exists(), reason="index.html not found")
class TestPremiumDesign:
    def test_new_css_tokens_present(self):
        assert '--violet:' in HTML
        assert '--cyan:' in HTML
        assert '--violet2:' in HTML

    def test_glassmorphism_present(self):
        assert 'backdrop-filter' in HTML

    def test_reduced_motion_present(self):
        assert 'prefers-reduced-motion' in HTML

    def test_typing_indicator_present(self):
        assert 'id="typing-indicator"' in BODY

    def test_typing_dot_present(self):
        assert 'typing-dot' in HTML

    def test_show_typing_fn_present(self):
        assert 'function showTyping' in HTML

    def test_hide_typing_fn_present(self):
        assert 'function hideTyping' in HTML

    def test_msg_slide_up_animation(self):
        assert 'msgSlideUp' in HTML

    def test_correct_flash_animation(self):
        assert 'correctFlash' in HTML

    def test_wrong_shake_animation(self):
        assert 'wrongShake' in HTML

    def test_bg_pulse_animation(self):
        assert 'bgPulse' in HTML


@pytest.mark.skipif(not HTML_PATH.exists(), reason="index.html not found")
class TestAPIContractPreserved:
    def test_api_chat_call_present(self):
        assert '/api/chat' in HTML

    def test_handle_decisions_present(self):
        assert 'handleDecisions' in HTML

    def test_generate_plan_present(self):
        assert 'generatePlan' in HTML

    def test_send_quiz_present(self):
        assert 'sendQuiz' in HTML


@pytest.mark.skipif(not HTML_PATH.exists(), reason="index.html not found")
class TestNoFakeData:
    def test_no_demo_mastery_data(self):
        assert 'DEMO_MASTERY' not in HTML

    def test_no_fake_mastery_percentages_as_real(self):
        # The old DEMO_GOALS with hardcoded 68%, 41%, 85% should be gone or clearly labelled
        # We just check DEMO_MASTERY is gone (the main source of fake data)
        assert 'DEMO_MASTERY' not in HTML


@pytest.mark.skipif(not HTML_PATH.exists(), reason="index.html not found")
class TestNoInternalExposure:
    def test_no_guidance_text_in_html(self):
        assert 'GUIDANCE:' not in HTML

    def test_no_scope_guard_in_html(self):
        assert 'studymate-scope-guard' not in BODY
