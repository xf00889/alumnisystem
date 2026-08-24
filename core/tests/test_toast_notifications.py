from pathlib import Path
from unittest import TestCase


BASE_DIR = Path(__file__).resolve().parents[2]


class ToastNotificationVisibilityTest(TestCase):
    def test_custom_notyf_types_use_the_supported_background_option(self):
        script = (
            BASE_DIR / "static" / "js" / "utils" / "toast-notifications.js"
        ).read_text(encoding="utf-8")

        self.assertNotIn("backgroundColor:", script)
        self.assertEqual(script.count("background: '#"), 4)

    def test_reduced_motion_keeps_notyf_content_visible(self):
        css = (
            BASE_DIR / "static" / "css" / "toast-notifications.css"
        ).read_text(encoding="utf-8")

        self.assertIn("@media (prefers-reduced-motion: reduce)", css)
        self.assertIn(".notyf .notyf__message", css)
        self.assertIn(".notyf__icon--warning::before", css)
        self.assertIn(".notyf__icon--info::before", css)
        self.assertIn("opacity: 1 !important;", css)
        self.assertIn(
            "transform: scale(1) translateY(-45%) translateX(13%) !important;",
            css,
        )

    def test_shared_stylesheet_is_loaded_by_each_public_shell(self):
        paths = [
            BASE_DIR / "templates" / "base.html",
            BASE_DIR / "templates" / "base_landingpage.html",
            BASE_DIR / "templates" / "components" / "auth_public_head.html",
        ]

        for path in paths:
            template = path.read_text(encoding="utf-8")
            self.assertIn("css/toast-notifications.css", template, str(path))
