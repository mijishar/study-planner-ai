"""Regression tests for StudyMate AI Home page layout.

Verifies:
1. All five remaining page divs have correct <div id="..."> HTML (no missing or extra <)
2. The Home page section does NOT contain the AI Tutor interface
3. The Student profile block is absent from the sidebar HTML
4. The Home page contains expected dashboard elements
5. The AI Tutor page exists and is separate from Home
6. Progress page is absent (removed in the premium upgrade)
"""

from __future__ import annotations
from pathlib import Path

import pytest

HTML_PATH = Path(__file__).resolve().parent.parent / "demo" / "static" / "index.html"
HTML = HTML_PATH.read_text(encoding="utf-8") if HTML_PATH.exists() else ""

# Progress page has been intentionally removed — only 5 pages remain
PAGES = [
    "page-home",
    "page-tutor",
    "page-planner",
    "page-myplans",
    "page-quiz",
]


@pytest.mark.skipif(not HTML_PATH.exists(), reason="index.html not found")
class TestPageBoundaries:
    """Every page div must open with exactly <div id="page-..." — no extra or missing <."""

    def _before(self, page_id: str) -> str:
        idx = HTML.find(f'id="{page_id}"')
        assert idx >= 5, f"Page '{page_id}' not found in HTML"
        return HTML[idx - 5 : idx]

    def test_page_home_boundary(self):
        assert self._before("page-home") == "<div ", \
            f"page-home has malformed opening tag: [{self._before('page-home')}]"

    def test_page_tutor_boundary(self):
        assert self._before("page-tutor") == "<div ", \
            f"page-tutor has malformed opening tag: [{self._before('page-tutor')}]"

    def test_page_planner_boundary(self):
        assert self._before("page-planner") == "<div ", \
            f"page-planner has malformed opening tag"

    def test_page_myplans_boundary(self):
        assert self._before("page-myplans") == "<div ", \
            f"page-myplans has malformed opening tag"

    def test_page_quiz_boundary(self):
        assert self._before("page-quiz") == "<div ", \
            f"page-quiz has malformed opening tag"

    def test_page_progress_boundary(self):
        """Progress page was intentionally removed in the premium upgrade."""
        assert 'id="page-progress"' not in HTML, \
            "page-progress should be absent after the upgrade removed it."

    def test_no_raw_html_text_page_tutor(self):
        """The string 'div id="page-tutor"' must never appear as bare text (without <)."""
        # It should appear exactly once, as part of '<div id="page-tutor"'
        raw_count = HTML.count('div id="page-tutor"')
        proper_count = HTML.count('<div id="page-tutor"')
        assert raw_count == proper_count, (
            "Raw 'div id=\"page-tutor\"' text found without leading '<' — "
            "this renders as visible text in the browser."
        )

    def test_no_raw_html_text_page_home(self):
        raw_count = HTML.count('div id="page-home"')
        proper_count = HTML.count('<div id="page-home"')
        assert raw_count == proper_count, (
            "Raw 'div id=\"page-home\"' text found without leading '<'."
        )


@pytest.mark.skipif(not HTML_PATH.exists(), reason="index.html not found")
class TestHomePageIsolation:
    """Home page section must contain only dashboard content — not AI Tutor interface."""

    @classmethod
    def _home_section(cls) -> str:
        home_start  = HTML.find('id="page-home"')
        tutor_start = HTML.find('id="page-tutor"')
        assert home_start >= 0, "page-home not found"
        assert tutor_start > home_start, "page-tutor must come after page-home"
        return HTML[home_start:tutor_start]

    def test_home_does_not_contain_tutor_form(self):
        assert "tutor-form" not in self._home_section(), \
            "Home page section contains AI Tutor form — pages are not properly isolated."

    def test_home_does_not_contain_tutor_log(self):
        assert 'id="tutor-log"' not in self._home_section(), \
            "Home page section contains AI Tutor conversation log."

    def test_home_does_not_contain_dec_panel(self):
        # The Decider panel (id="dec") belongs to the AI Tutor page, not Home
        assert 'id="dec"' not in self._home_section(), \
            "Home page section contains the Decider panel (should be in AI Tutor only)."

    def test_home_contains_streak_card(self):
        assert "streak-card" in self._home_section(), \
            "Home page is missing the study streak card."

    def test_home_contains_quote_banner(self):
        assert "quote-banner" in self._home_section(), \
            "Home page is missing the daily quote banner."

    def test_home_contains_quick_actions(self):
        assert "qa-grid" in self._home_section() or "qa-card" in self._home_section(), \
            "Home page is missing quick actions."

    def test_home_contains_stats_bar(self):
        assert "top-stats-bar" in self._home_section(), \
            "Home page is missing the top stats bar."


@pytest.mark.skipif(not HTML_PATH.exists(), reason="index.html not found")
class TestSidebarStudentProfile:
    """The Student profile block must be absent from the sidebar HTML."""

    def test_student_label_absent(self):
        # "Student" as a label/name inside sb-user div should be gone
        assert "sb-user-name" not in HTML or \
               HTML.index("sb-user-name") < HTML.index("</style>"), (
            "sb-user-name found in HTML body — Student profile not fully removed."
        )

    def test_sb_footer_html_absent(self):
        """sb-footer must not appear as an HTML element (CSS class is OK)."""
        # Find any <div class="sb-footer" in the HTML body (after </style>)
        style_end = HTML.find("</style>")
        html_body = HTML[style_end:] if style_end >= 0 else HTML
        assert '<div class="sb-footer"' not in html_body, \
            "Student profile <div class='sb-footer'> still present in HTML body."

    def test_sb_avatar_html_absent(self):
        style_end = HTML.find("</style>")
        html_body = HTML[style_end:] if style_end >= 0 else HTML
        assert 'class="sb-avatar"' not in html_body, \
            "Student avatar element still present in HTML body."

    def test_sidebar_logo_present(self):
        assert "sb-logo" in HTML, "Sidebar logo must remain."

    def test_sidebar_nav_present(self):
        assert "sb-nav" in HTML, "Sidebar navigation must remain."

    def test_sb_meta_present(self):
        assert 'id="sb-meta"' in HTML, \
            "sb-meta (AI model info) should still be present in the sidebar."

    def test_all_nav_items_present(self):
        for page in ["home", "tutor", "planner", "myplans", "quiz"]:
            assert f'data-page="{page}"' in HTML, \
                f"Nav item for '{page}' is missing from the sidebar."

    def test_progress_nav_item_absent(self):
        """Progress nav item removed in the premium upgrade."""
        assert 'data-page="progress"' not in HTML, \
            "Progress nav item should be absent after the upgrade."


@pytest.mark.skipif(not HTML_PATH.exists(), reason="index.html not found")
class TestAITutorPageIntact:
    """AI Tutor page must still exist and be structurally complete."""

    def test_tutor_page_exists(self):
        assert 'id="page-tutor"' in HTML

    def test_tutor_form_in_tutor_page(self):
        tutor_start   = HTML.find('id="page-tutor"')
        planner_start = HTML.find('id="page-planner"')
        tutor_section = HTML[tutor_start:planner_start]
        assert "tutor-form" in tutor_section, \
            "AI Tutor form must be inside the page-tutor section."

    def test_dec_panel_in_tutor_page(self):
        tutor_start   = HTML.find('id="page-tutor"')
        planner_start = HTML.find('id="page-planner"')
        tutor_section = HTML[tutor_start:planner_start]
        assert 'id="dec"' in tutor_section, \
            "Strands Decider panel must be inside the page-tutor section."
