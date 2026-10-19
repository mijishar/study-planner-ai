"""Regression tests for the full StudyMate AI premium upgrade features.

Covers Resources page, Settings page, Focus Timer, Top Bar, Welcome Banner,
Theme system, Profile settings, and nav correctness.
"""

from pathlib import Path
import pytest

HTML_PATH = Path(__file__).resolve().parent.parent / "demo" / "static" / "index.html"
HTML = HTML_PATH.read_text(encoding="utf-8") if HTML_PATH.exists() else ""
STYLE_END = HTML.find("</style>")
BODY = HTML[STYLE_END:] if STYLE_END >= 0 else HTML


@pytest.mark.skipif(not HTML_PATH.exists(), reason="index.html not found")
class TestNewNavItems:
    def test_resources_nav_present(self):    assert 'data-page="resources"' in BODY
    def test_settings_nav_present(self):     assert 'data-page="settings"' in BODY
    def test_progress_nav_absent(self):      assert 'data-page="progress"' not in BODY


@pytest.mark.skipif(not HTML_PATH.exists(), reason="index.html not found")
class TestResourcesPage:
    def _resources(self):
        s = HTML.find('id="page-resources"')
        e = HTML.find('id="page-settings"')
        return HTML[s:e] if s >= 0 and e > s else ""

    def test_resources_page_exists(self):         assert 'id="page-resources"' in HTML
    def test_resources_has_mdn(self):              assert "developer.mozilla.org" in self._resources()
    def test_resources_has_freecodecamp(self):     assert "freecodecamp.org" in self._resources()
    def test_resources_has_khan_academy(self):     assert "khanacademy.org" in self._resources()
    def test_resources_has_fastai(self):           assert "fast.ai" in self._resources()
    def test_resources_has_anki(self):             assert "apps.ankiweb.net" in self._resources()
    def test_resources_has_disclaimer(self):       assert "not affiliated" in self._resources()
    def test_resources_links_open_new_tab(self):   assert 'target="_blank"' in self._resources()
    def test_resources_rel_noopener(self):         assert "noopener" in self._resources()


@pytest.mark.skipif(not HTML_PATH.exists(), reason="index.html not found")
class TestSettingsPage:
    def _settings(self):
        s = HTML.find('id="page-settings"')
        e = HTML.find('</div><!-- #app -->')
        return HTML[s:e] if s >= 0 and e > s else HTML[s:]

    def test_settings_page_exists(self):           assert 'id="page-settings"' in HTML
    def test_settings_has_appearance_tab(self):    assert "Appearance" in self._settings()
    def test_settings_has_profile_tab(self):       assert "Profile" in self._settings()
    def test_settings_has_learning_tab(self):      assert "Learning" in self._settings()
    def test_settings_has_dark_theme_option(self): assert 'data-theme-val="dark"' in self._settings()
    def test_settings_has_bright_theme_option(self): assert 'data-theme-val="bright"' in self._settings()
    def test_settings_has_system_theme_option(self): assert 'data-theme-val="system"' in self._settings()
    def test_settings_has_avatar_options(self):    assert "avatar-option" in self._settings()
    def test_settings_has_save_profile_btn(self):  assert "saveProfile" in self._settings()
    def test_settings_has_local_storage_note(self): assert "browser only" in self._settings()
    def test_settings_has_study_goal_slider(self): assert 'id="learn-goal"' in self._settings()


@pytest.mark.skipif(not HTML_PATH.exists(), reason="index.html not found")
class TestFocusTimer:
    def test_timer_card_exists(self):            assert "focus-timer-card" in BODY
    def test_timer_ring_svg_exists(self):        assert 'id="timer-ring"' in BODY
    def test_timer_display_exists(self):         assert 'id="focus-timer-display"' in BODY
    def test_timer_start_btn_exists(self):       assert 'id="timer-start-btn"' in BODY
    def test_timer_toggle_fn_exists(self):       assert "function timerToggle" in HTML
    def test_timer_reset_fn_exists(self):        assert "function timerReset" in HTML
    def test_timer_update_display_fn_exists(self): assert "function timerUpdateDisplay" in HTML
    def test_timer_duration_input_exists(self):  assert 'id="timer-duration-input"' in BODY
    def test_timer_complete_msg_exists(self):    assert 'id="timer-complete-msg"' in BODY
    def test_timer_status_label_exists(self):    assert 'id="timer-status-label"' in BODY


@pytest.mark.skipif(not HTML_PATH.exists(), reason="index.html not found")
class TestTopBar:
    def test_topbar_exists(self):                assert 'id="topbar"' in BODY
    def test_topbar_search_exists(self):         assert 'id="topbar-search"' in BODY
    def test_topbar_avatar_exists(self):         assert 'id="topbar-avatar-display"' in BODY
    def test_topbar_routes_to_tutor(self):       assert "nav('tutor')" in HTML or 'nav("tutor")' in HTML
    def test_topbar_css_present(self):           assert "#topbar" in HTML


@pytest.mark.skipif(not HTML_PATH.exists(), reason="index.html not found")
class TestWelcomeBanner:
    def test_welcome_banner_exists(self):        assert "welcome-banner" in BODY
    def test_wb_greeting_exists(self):           assert 'id="wb-greeting"' in BODY
    def test_wb_date_exists(self):               assert 'id="wb-date"' in BODY
    def test_wb_quote_exists(self):              assert 'id="wb-quote"' in BODY
    def test_wb_illustration_exists(self):       assert "wb-illustration" in BODY
    def test_wb_orbs_present(self):              assert "wb-orb" in BODY
    def test_wb_cta_buttons(self):               assert "Ask AI Now" in BODY


@pytest.mark.skipif(not HTML_PATH.exists(), reason="index.html not found")
class TestThemeSystem:
    def test_light_theme_css_present(self):      assert '[data-theme="bright"]' in HTML
    def test_apply_theme_fn_exists(self):        assert "function applyTheme" in HTML
    def test_select_theme_fn_exists(self):       assert "function selectTheme" in HTML
    def test_theme_persisted_to_localstorage(self): assert "sm_theme" in HTML
    def test_light_theme_body_override(self):    assert 'background: #f0f4f8' in HTML
    def test_light_theme_card_override(self):    assert "rgba(255,255,255,.95)" in HTML


@pytest.mark.skipif(not HTML_PATH.exists(), reason="index.html not found")
class TestProfileSettings:
    def test_open_settings_tab_fn_exists(self):  assert "function openSettingsTab" in HTML
    def test_save_profile_fn_exists(self):       assert "function saveProfile" in HTML
    def test_load_profile_fn_exists(self):       assert "function loadProfileForm" in HTML
    def test_select_avatar_fn_exists(self):      assert "function selectAvatar" in HTML
    def test_profile_persisted(self):            assert "sm_profile" in HTML
    def test_save_learning_prefs_fn_exists(self): assert "function saveLearningPrefs" in HTML
    def test_learning_prefs_persisted(self):     assert "sm_learning_prefs" in HTML


@pytest.mark.skipif(not HTML_PATH.exists(), reason="index.html not found")
class TestPageBoundariesAll7:
    """All 7 pages (home, tutor, planner, myplans, quiz, resources, settings) must be clean."""

    PAGES = ["page-home", "page-tutor", "page-planner", "page-myplans",
             "page-quiz", "page-resources", "page-settings"]

    def test_all_seven_pages_present(self):
        for pg in self.PAGES:
            assert HTML.find(f'id="{pg}"') >= 0, f"Missing: {pg}"

    def test_all_seven_boundaries_clean(self):
        for pg in self.PAGES:
            idx = HTML.find(f'id="{pg}"')
            assert idx >= 5, f"{pg} not found"
            before = HTML[idx-5:idx]
            assert before == "<div ", f"{pg} boundary broken: [{before}]"

    def test_api_chat_preserved(self):           assert "/api/chat" in HTML
    def test_handle_decisions_preserved(self):   assert "handleDecisions" in HTML
    def test_dec_in_dom(self):                   assert 'id="dec"' in HTML
    def test_generate_plan_preserved(self):      assert "generatePlan" in HTML
    def test_send_quiz_preserved(self):          assert "sendQuiz" in HTML
