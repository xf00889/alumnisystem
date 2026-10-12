import shutil
import tempfile
from datetime import date

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from alumni_directory.models import Alumni
from accounts.forms import EducationForm, EducationFormSet, ExperienceForm
from accounts.models import Education, Experience


PROFILE_TEST_MIDDLEWARE = [
    middleware
    for middleware in settings.MIDDLEWARE
    if middleware != "setup.middleware.SetupRequiredMiddleware"
]


@override_settings(MIDDLEWARE=PROFILE_TEST_MIDDLEWARE)
class ProfileRemediationTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model

        self.media_root = tempfile.mkdtemp(prefix="alumni-profile-tests-")
        self.media_override = override_settings(MEDIA_ROOT=self.media_root)
        self.media_override.enable()

        User = get_user_model()
        self.user = User.objects.create_user(
            "profile-user",
            "profile@example.com",
            "pass",
            first_name="Profile",
            last_name="User",
        )
        self.user.profile.has_completed_registration = True
        self.user.profile.save(update_fields=["has_completed_registration"])
        self.alumni = Alumni.objects.create(
            user=self.user,
            college="CTE",
            campus="MAIN",
            graduation_year=1999,
            course="BSED",
            major="MATHEMATICS",
            gender="M",
            province="Negros Oriental",
            city="Dumaguete",
            address="Address",
        )
        self.primary = Education.objects.create(
            profile=self.user.profile,
            program="BSED-MATH",
            major="MATHEMATICS",
            school="NORSU-MAIN",
            graduation_year=1999,
            is_primary=True,
        )
        self.client.force_login(self.user)

    def tearDown(self):
        self.media_override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    @staticmethod
    def _management_data(education_total=0, experience_total=0, skill_total=0):
        data = {}
        for prefix, total in (
            ("education", education_total),
            ("experience", experience_total),
            ("skill", skill_total),
        ):
            data.update({
                f"{prefix}-TOTAL_FORMS": str(total),
                f"{prefix}-INITIAL_FORMS": "0",
                f"{prefix}-MIN_NUM_FORMS": "0",
                f"{prefix}-MAX_NUM_FORMS": "1000",
            })
        return data

    def test_experience_location_is_optional_and_profile_get_is_read_only(self):
        form = ExperienceForm(data={
            "company": "Acme",
            "position": "Engineer",
            "location": "",
            "start_date": "2020-01-01",
            "career_significance": "REGULAR",
        })
        self.assertTrue(form.is_valid(), form.errors)

        self.user.profile.current_position = "Engineer"
        self.user.profile.current_employer = "Acme"
        self.user.profile.save(update_fields=["current_position", "current_employer"])
        self.assertFalse(Experience.objects.filter(profile=self.user.profile).exists())
        self.client.get(reverse("accounts:profile_detail"))
        self.assertFalse(Experience.objects.filter(profile=self.user.profile).exists())

    def test_server_templates_render_one_avatar_and_real_empty_forms(self):
        response = self.client.get(reverse("accounts:profile_update"))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertEqual(html.count('id="id_avatar"'), 1)
        self.assertIn('id="education-empty-form"', html)
        self.assertIn('name="education-__prefix__-program"', html)
        self.assertIn('name="experience-__prefix__-location"', html)
        self.assertIn('name="skill-__prefix__-proficiency_level"', html)

    def test_only_primary_education_synchronizes_alumni_academics(self):
        form = EducationForm(
            data={
                "campus": "NORSU-BSC",
                "college": "CAS",
                "program": "BSCS",
                "major": "AI",
                "graduation_year": 2003,
                "achievements": "",
            },
            instance=self.primary,
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.alumni.refresh_from_db()
        self.assertEqual(
            (
                self.alumni.campus,
                self.alumni.college,
                self.alumni.course,
                self.alumni.major,
                self.alumni.graduation_year,
            ),
            ("BSC", "CAS", "BSCS", "AI", 2003),
        )

        secondary = Education.objects.create(
            profile=self.user.profile,
            program="BSED",
            school="NORSU-MAIN",
            graduation_year=2010,
            is_primary=False,
        )
        secondary_form = EducationForm(
            data={
                "campus": "NORSU-SIA",
                "college": "CTE",
                "program": "BSED",
                "major": "SCIENCE",
                "graduation_year": 2010,
                "achievements": "",
            },
            instance=secondary,
        )
        self.assertTrue(secondary_form.is_valid(), secondary_form.errors)
        secondary_form.save()
        self.alumni.refresh_from_db()
        self.assertEqual((self.alumni.campus, self.alumni.course), ("BSC", "BSCS"))

    def test_primary_education_deletion_is_rejected_by_formset(self):
        data = {
            "education-TOTAL_FORMS": "1",
            "education-INITIAL_FORMS": "1",
            "education-MIN_NUM_FORMS": "0",
            "education-MAX_NUM_FORMS": "1000",
            "education-0-id": str(self.primary.id),
            "education-0-campus": "NORSU-MAIN",
            "education-0-college": "CTE",
            "education-0-program": "BSED-MATH",
            "education-0-major": "MATHEMATICS",
            "education-0-graduation_year": "1999",
            "education-0-achievements": "",
            "education-0-DELETE": "on",
        }
        formset = EducationFormSet(data, instance=self.user.profile, prefix="education")
        self.assertFalse(formset.is_valid())
        self.assertIn("Primary education cannot be deleted", str(formset.non_form_errors()))
        self.assertTrue(Education.objects.filter(pk=self.primary.pk).exists())

    def test_structured_errors_identify_section_row_and_field(self):
        data = self._management_data(experience_total=1)
        data.update({
            "first_name": "Profile",
            "last_name": "User",
            "experience-0-company": "Acme",
            "experience-0-position": "",
            "experience-0-location": "",
            "experience-0-start_date": "2020-01-01",
            "experience-0-career_significance": "REGULAR",
        })
        response = self.client.post(reverse("accounts:profile_update"), data)
        self.assertEqual(response.status_code, 400)
        error = next(
            item for item in response.json()["errors"]
            if item["section"] == "experience" and item["field"] == "position"
        )
        self.assertEqual(error["row"], 0)
        self.assertTrue(error["messages"])

    def test_avatar_upload_is_saved_displayed_and_removed_only_on_save(self):
        data = self._management_data()
        data.update({"first_name": "Profile", "last_name": "User"})
        gif = (
            b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00"
            b"\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
        )
        data["avatar"] = SimpleUploadedFile("avatar.gif", gif, content_type="image/gif")
        response = self.client.post(reverse("accounts:profile_update"), data)
        self.assertEqual(response.status_code, 200, response.content)
        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.avatar.name)
        self.assertContains(self.client.get(reverse("accounts:profile_detail")), self.user.profile.avatar.url)

        remove_data = self._management_data()
        remove_data.update({
            "first_name": "Profile",
            "last_name": "User",
            "remove_avatar": "true",
        })
        response = self.client.post(reverse("accounts:profile_update"), remove_data)
        self.assertEqual(response.status_code, 200, response.content)
        self.user.profile.refresh_from_db()
        self.assertFalse(self.user.profile.avatar)
