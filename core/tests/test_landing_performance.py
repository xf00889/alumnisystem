from pathlib import Path
from unittest.mock import patch

from django.test import SimpleTestCase
from PIL import Image

from core.recaptcha_widgets import DatabaseReCaptchaV3


BASE_DIR = Path(__file__).resolve().parents[2]


class LandingAssetPerformanceTest(SimpleTestCase):
    def test_delivery_images_are_right_sized_webp_assets(self):
        specs = {
            'bg.webp': {'max_width': 1920, 'max_bytes': 100_000},
            'logo_norsu.webp': {'max_width': 256, 'max_bytes': 60_000},
            'alumni_logo.webp': {'max_width': 256, 'max_bytes': 60_000},
        }

        for filename, limits in specs.items():
            path = BASE_DIR / 'static' / 'images' / filename
            self.assertTrue(path.exists(), filename)
            self.assertLessEqual(path.stat().st_size, limits['max_bytes'], filename)
            with Image.open(path) as image:
                self.assertEqual(image.format, 'WEBP', filename)
                self.assertLessEqual(image.width, limits['max_width'], filename)

    def test_public_shell_preloads_lcp_asset_and_loads_motion_policy_last(self):
        template = (
            BASE_DIR / 'templates' / 'base_landingpage.html'
        ).read_text(encoding='utf-8')

        self.assertIn("static 'images/bg.webp'", template)
        self.assertIn('as="image" type="image/webp" fetchpriority="high"', template)
        self.assertIn("static 'css/landing-performance.css'", template)
        self.assertIn('<body class="public-landing">', template)
        self.assertGreater(
            template.index("static 'css/landing-performance.css'"),
            template.index('{% block extra_head %}'),
        )

    def test_public_landing_templates_do_not_request_legacy_background(self):
        paths = [
            BASE_DIR / 'templates' / 'home.html',
            BASE_DIR / 'templates' / 'landing' / 'about_us.html',
            BASE_DIR / 'templates' / 'landing' / 'contact_us.html',
            BASE_DIR / 'templates' / 'landing' / 'events.html',
            BASE_DIR / 'jobs' / 'templates' / 'jobs' / 'careers.html',
            BASE_DIR / 'templates' / 'components' / 'hero_section.html',
        ]

        for path in paths:
            source = path.read_text(encoding='utf-8')
            self.assertNotIn('images/bg.jpg', source, str(path))
            self.assertIn('images/bg.webp', source, str(path))


class LandingMotionPerformanceTest(SimpleTestCase):
    def test_hero_content_is_not_delayed_by_staggered_entrance_animation(self):
        css = (
            BASE_DIR / 'static' / 'css' / 'hero_section.css'
        ).read_text(encoding='utf-8')
        home = (
            BASE_DIR / 'templates' / 'home.html'
        ).read_text(encoding='utf-8')
        slider = (
            BASE_DIR / 'static' / 'js' / 'officials_slider.js'
        ).read_text(encoding='utf-8')

        self.assertNotIn('heroFadeInUp', css)
        self.assertNotIn("new IntersectionObserver", home)
        self.assertNotIn("new IntersectionObserver", slider)
        self.assertIn("sliderContainer.classList.add('in-view')", slider)

    def test_shared_motion_policy_honors_reduced_motion(self):
        css = (
            BASE_DIR / 'static' / 'css' / 'landing-performance.css'
        ).read_text(encoding='utf-8')

        self.assertIn('@media (prefers-reduced-motion: reduce)', css)
        self.assertIn('transition: none !important;', css)
        self.assertIn('background-attachment: scroll !important;', css)


class LazyReCaptchaV3WidgetTest(SimpleTestCase):
    @patch('core.recaptcha_widgets.is_recaptcha_enabled', return_value=True)
    @patch(
        'core.recaptcha_widgets.get_recaptcha_public_key',
        return_value='test-site-key',
    )
    def test_widget_defers_google_api_and_uses_one_v3_controller(
        self,
        _public_key,
        _enabled,
    ):
        widget = DatabaseReCaptchaV3(action='feedback')
        html = widget.render('captcha', None)

        self.assertIn('class="norsu-recaptcha-v3"', html)
        self.assertIn('data-recaptcha-action="feedback"', html)
        self.assertIn('data-sitekey="test-site-key"', html)
        self.assertIn('js/lazy-recaptcha-v3.js', html)
        self.assertNotIn('google.com/recaptcha/api.js', html)
        self.assertNotIn('class="g-recaptcha"', html)

    def test_lazy_controller_does_not_submit_when_verification_fails(self):
        script = (
            BASE_DIR / 'static' / 'js' / 'lazy-recaptcha-v3.js'
        ).read_text(encoding='utf-8')

        self.assertIn('HTMLFormElement.prototype.submit.call(form);', script)
        self.assertIn('Security verification unavailable', script)
        self.assertIn('this.reportError(field);', script)
