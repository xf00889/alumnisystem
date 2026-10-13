"""Source-level feature parity for public UI refinements; run without Django installed."""
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
def read(path): return (ROOT / path).read_text(encoding='utf-8')
class PublicRefinementTests(unittest.TestCase):
    def test_shared_typography_is_public_only(self):
        base = read('templates/base_landingpage.html')
        css = read('static/css/public_typography.css')
        self.assertIn("versioned_static 'css/public_typography.css'", base)
        self.assertIn('body.public-landing', css)
        self.assertNotIn('body.alumni', css)
        self.assertNotIn('html { font-size:', css)

    def test_goals_and_values_remain_dynamic_and_use_full_width(self):
        home = read('templates/home.html')
        css = read('static/css/home_experience.css')
        self.assertIn('vmgo_section.goals|format_acronym', home)
        self.assertIn('vmgo_section.core_values|format_acronym', home)
        self.assertIn('.home-experience .home-framework-content > section', css)
        self.assertIn('grid-template-columns: repeat(3, minmax(0, 1fr))', css)

    def test_team_is_manual_carousel_with_keyboard_support(self):
        home = read('templates/home.html')
        js = read('static/js/home_gallery.js')
        self.assertIn('data-team-gallery data-home-gallery data-gallery-autoplay="false"', home)
        team_controls = home.split('class="home-team-controls')[1].split('</div>')[0]
        self.assertNotIn('data-gallery-toggle', team_controls)
        self.assertIn('data-team-previous', team_controls)
        self.assertIn('data-team-next', team_controls)
        self.assertIn("if (!track || !items.length || !prev || !next) return", js)
        self.assertIn("'keydown'", js)
        self.assertIn('if (!toggle) return;', js)

    def test_feedback_preserves_processor_and_new_layout(self):
        home = read('templates/home.html')
        self.assertIn('home-help-layout-feedback-only', home)
        self.assertIn('home-help-guidance', home)
        self.assertIn("{% url 'core:contact_us' %}", home)
        for marker in ('{% csrf_token %}', 'name="feedback_submit"', 'name="office_website"',
                       'feedback_form.category', 'feedback_form.priority', 'feedback_form.subject',
                       'feedback_form.message', 'feedback_form.attachment', 'feedback_form.captcha'):
            self.assertIn(marker,home)

    def test_about_objective_content_and_consistent_cards(self):
        vmgo = read('templates/components/vmgo_section.html')
        css = read('static/css/vmgo_section.css')
        for n in range(1, 5): self.assertIn('vmgo_section.quality_objective_'+str(n), vmgo)
        self.assertIn('vmgo_section.quality_objectives_footer',vmgo)
        self.assertIn('.vmgo-section .quality-objective-card', css)
        self.assertIn('grid-template-columns: repeat(4,minmax(0,1fr))', css)
        self.assertIn('grid-template-columns: minmax(0,1fr)', css)

if __name__ == '__main__': unittest.main()
