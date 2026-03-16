"""
Seed realistic sample data for list-heavy pages.

Creates:
- Alumni groups (+ memberships)
- Events
- Announcements (+ categories)

The command is idempotent for generated records because it uses stable
titles/names with a configurable prefix.
"""

from datetime import timedelta
import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models.signals import post_delete
from django.utils import timezone
from django.utils.text import slugify

from alumni_groups.models import AlumniGroup, GroupMembership
from alumni_groups.models import GroupActivity
from alumni_groups.signals import update_analytics_on_member_leave
from announcements.models import Announcement, Category
from events.models import Event

User = get_user_model()


class Command(BaseCommand):
    help = "Seed realistic sample announcements, events, and groups for list pages."

    DEFAULT_PREFIX = "[SEED]"
    USERNAME_PREFIX = "seed_alumni_"
    SEED_MARKER = "Seeded by seed_sample_content command."

    ANNOUNCEMENT_CATEGORY_DATA = [
        ("Campus News", "Updates from campus leadership and alumni office."),
        ("Events", "Upcoming activities for alumni and students."),
        ("Career Opportunities", "Jobs, internships, and career development programs."),
        ("Alumni Spotlight", "Stories and achievements from alumni."),
        ("Fundraising", "Scholarship and university support campaigns."),
        ("Volunteer Opportunities", "Community and outreach opportunities."),
        ("Academic Updates", "Program and curriculum related announcements."),
        ("Community Service", "Extension programs and service initiatives."),
    ]

    PROGRAMS = [
        "BS Information Technology",
        "BS Computer Science",
        "BS Information Systems",
        "BS Accountancy",
        "BS Business Administration",
        "BS Criminology",
        "BS Nursing",
        "BS Psychology",
        "BS Hospitality Management",
        "BS Tourism Management",
    ]

    GROUP_FOCUS_AREAS = [
        "peer mentoring",
        "career opportunities",
        "industry networking",
        "community outreach",
        "professional certification prep",
        "research collaboration",
        "startup and innovation support",
        "board exam coaching",
    ]

    EVENT_THEMES = [
        "Alumni Homecoming and Networking Night",
        "Career Talk: Future Skills for Global Work",
        "Resume and Portfolio Clinic",
        "Industry Panel: Trends and Opportunities",
        "Leadership and Communication Workshop",
        "Mentorship Orientation Session",
        "Startup Pitch and Founders Forum",
        "Community Service Planning Meeting",
        "Alumni Chapters Coordination Summit",
        "Graduate School and Scholarship Briefing",
        "Technical Skills Bootcamp",
        "Women in Leadership Roundtable",
        "International Alumni Connect",
        "Professional Ethics and Workplace Culture",
        "Campus-Industry Partnership Forum",
    ]

    EVENT_VENUES = [
        "NORSU Main Campus Conference Hall",
        "Alumni Affairs Function Room",
        "Student Center Multipurpose Hall",
        "NORSU Bais Campus Auditorium",
        "NORSU Guihulngan Campus AVR",
        "NORSU Siaton Campus Hall",
        "Dumaguete City Convention Center",
        "Hybrid Hub and Learning Commons",
    ]

    ANNOUNCEMENT_TOPICS = [
        "Application Window for Alumni Leadership Program",
        "Call for Mentors for Graduating Students",
        "Registration Now Open for Career Fair",
        "Updated Guidelines for Alumni ID Verification",
        "New Scholarship Sponsorship Drive",
        "Quarterly Community Outreach Participation",
        "Volunteer Leads Needed for Regional Chapters",
        "Submission Deadline for Alumni Success Stories",
        "Campus Partnership Program Expansion",
        "Industry Certification Subsidy Slots Available",
        "Career Services One-on-One Coaching Schedule",
        "Regional Alumni Chapter Activation Notice",
        "Professional Development Webinar Series",
        "University Anniversary Participation Guidelines",
        "Annual Data Update and Directory Refresh",
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--announcements",
            type=int,
            default=18,
            help="Number of sample announcements to seed (default: 18).",
        )
        parser.add_argument(
            "--events",
            type=int,
            default=15,
            help="Number of sample events to seed (default: 15).",
        )
        parser.add_argument(
            "--groups",
            type=int,
            default=12,
            help="Number of sample groups to seed (default: 12).",
        )
        parser.add_argument(
            "--users",
            type=int,
            default=24,
            help="Number of reusable seed users for creators/members (default: 24).",
        )
        parser.add_argument(
            "--password",
            default="SeedPass123!",
            help="Password applied to seed users (default: SeedPass123!).",
        )
        parser.add_argument(
            "--prefix",
            default=self.DEFAULT_PREFIX,
            help=f"Prefix for seeded records (default: {self.DEFAULT_PREFIX}).",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=20260316,
            help="Deterministic random seed value (default: 20260316).",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete previously seeded records (matching prefix) before seeding.",
        )
        parser.add_argument(
            "--reset-users",
            action="store_true",
            help="Also delete generated seed users (username starts with seed_alumni_).",
        )

    def handle(self, *args, **options):
        announcements_count = options["announcements"]
        events_count = options["events"]
        groups_count = options["groups"]
        users_count = options["users"]
        password = options["password"]
        seed_value = options["seed"]
        prefix = (options["prefix"] or self.DEFAULT_PREFIX).strip()

        self._validate_options(
            announcements_count=announcements_count,
            events_count=events_count,
            groups_count=groups_count,
            users_count=users_count,
        )

        if not prefix:
            prefix = self.DEFAULT_PREFIX

        self.random = random.Random(seed_value)

        self.stdout.write(self.style.SUCCESS("Starting sample content seeding..."))
        self.stdout.write(f"Prefix: {prefix}")
        self.stdout.write(f"Random seed: {seed_value}")
        self.stdout.write("")

        with transaction.atomic():
            if options["reset"]:
                reset_stats = self._reset_seed_data(
                    prefix=prefix,
                    reset_users=options["reset_users"],
                )
                self.stdout.write("Reset complete:")
                self.stdout.write(f"  - Announcements deleted: {reset_stats['announcements']}")
                self.stdout.write(f"  - Events deleted: {reset_stats['events']}")
                self.stdout.write(f"  - Groups deleted: {reset_stats['groups']}")
                self.stdout.write(f"  - Users deleted: {reset_stats['users']}")
                self.stdout.write("")

            users, user_stats = self._ensure_seed_users(users_count, password)
            categories, category_stats = self._ensure_categories()
            groups, group_stats = self._ensure_groups(prefix, groups_count, users)
            membership_stats = self._ensure_memberships(groups, users)
            events, event_stats = self._ensure_events(prefix, events_count, users, groups)
            announcement_stats = self._ensure_announcements(
                prefix,
                announcements_count,
                categories,
            )

        self.stdout.write(self.style.SUCCESS("Seeding finished."))
        self.stdout.write("")
        self.stdout.write("Summary")
        self.stdout.write("-------")
        self.stdout.write(
            f"Users: created={user_stats['created']}, existing={user_stats['existing']}"
        )
        self.stdout.write(
            f"Categories: created={category_stats['created']}, "
            f"updated={category_stats['updated']}, existing={category_stats['existing']}"
        )
        self.stdout.write(
            f"Groups: created={group_stats['created']}, existing={group_stats['existing']}"
        )
        self.stdout.write(
            f"Memberships: created={membership_stats['created']}, "
            f"existing={membership_stats['existing']}"
        )
        self.stdout.write(
            f"Events: created={event_stats['created']}, existing={event_stats['existing']}"
        )
        self.stdout.write(
            f"Announcements: created={announcement_stats['created']}, "
            f"existing={announcement_stats['existing']}"
        )
        self.stdout.write("")
        self.stdout.write("Seed users login")
        self.stdout.write("----------------")
        self.stdout.write(f"Username pattern: {self.USERNAME_PREFIX}01 ...")
        self.stdout.write(f"Password: {password}")
        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Review /groups/, /events/, and /announcements/."
            )
        )

    def _validate_options(self, announcements_count, events_count, groups_count, users_count):
        values = {
            "--announcements": announcements_count,
            "--events": events_count,
            "--groups": groups_count,
            "--users": users_count,
        }
        for option_name, value in values.items():
            if value < 0:
                raise CommandError(f"{option_name} must be zero or greater.")
        if users_count < 1 and (groups_count > 0 or events_count > 0):
            raise CommandError("--users must be at least 1 when creating groups/events.")

    def _reset_seed_data(self, prefix, reset_users=False):
        announcement_deleted, _ = Announcement.objects.filter(
            title__startswith=f"{prefix} Announcement "
        ).delete()
        event_deleted, _ = Event.objects.filter(
            title__startswith=f"{prefix} Event "
        ).delete()
        seed_group_ids = list(
            AlumniGroup.objects.filter(
                name__startswith=f"{prefix} Group "
            ).values_list("id", flat=True)
        )

        group_deleted = 0
        if seed_group_ids:
            # GroupMembership post_delete creates GroupActivity records.
            # Temporarily disconnect it so reset cleanup does not recreate rows
            # while parent groups are being removed.
            post_delete.disconnect(
                update_analytics_on_member_leave,
                sender=GroupMembership,
            )
            try:
                GroupMembership.objects.filter(group_id__in=seed_group_ids).delete()
            finally:
                post_delete.connect(
                    update_analytics_on_member_leave,
                    sender=GroupMembership,
                )

            GroupActivity.objects.filter(group_id__in=seed_group_ids).delete()
            group_deleted, _ = AlumniGroup.objects.filter(
                id__in=seed_group_ids
            ).delete()

        user_deleted = 0
        if reset_users:
            user_deleted, _ = User.objects.filter(
                username__startswith=self.USERNAME_PREFIX
            ).delete()

        return {
            "announcements": announcement_deleted,
            "events": event_deleted,
            "groups": group_deleted,
            "users": user_deleted,
        }

    def _ensure_seed_users(self, count, password):
        users = []
        created = 0
        existing = 0

        for index in range(1, count + 1):
            username = f"{self.USERNAME_PREFIX}{index:02d}"
            defaults = {
                "email": f"{username}@example.com",
                "first_name": f"Seed{index:02d}",
                "last_name": "Alumni",
            }
            user, was_created = User.objects.get_or_create(
                username=username,
                defaults=defaults,
            )

            if was_created:
                user.set_password(password)
                user.save(update_fields=["password"])
                created += 1
            else:
                existing += 1
                if not user.check_password(password):
                    user.set_password(password)
                    user.save(update_fields=["password"])

            self._mark_profile_complete_if_present(user)
            users.append(user)

        return users, {"created": created, "existing": existing}

    def _mark_profile_complete_if_present(self, user):
        try:
            profile = user.profile
        except Exception:
            return

        if not profile.has_completed_registration:
            profile.has_completed_registration = True
            profile.save(update_fields=["has_completed_registration"])

    def _ensure_categories(self):
        categories = []
        created = 0
        updated = 0
        existing = 0

        for name, description in self.ANNOUNCEMENT_CATEGORY_DATA:
            slug = slugify(name)
            category, was_created = Category.objects.get_or_create(
                slug=slug,
                defaults={"name": name, "description": description},
            )
            if was_created:
                created += 1
            else:
                existing += 1
            categories.append(category)

        return categories, {"created": created, "updated": updated, "existing": existing}

    def _ensure_groups(self, prefix, count, users):
        groups = []
        created = 0
        existing = 0

        campus_choices = list(AlumniGroup.CAMPUS_CHOICES)
        campus_labels = dict(campus_choices)
        now_year = timezone.now().year

        for index in range(1, count + 1):
            program = self.random.choice(self.PROGRAMS)
            focus_area = self.random.choice(self.GROUP_FOCUS_AREAS)
            campus_code, _ = self.random.choice(campus_choices)
            campus_short = (
                campus_labels[campus_code]
                .replace("NORSU ", "")
                .replace(" Campus", "")
            )

            batch_end_year = now_year - self.random.randint(0, 10)
            batch_start_year = batch_end_year - self.random.choice([3, 4, 5])

            name = (
                f"{prefix} Group {index:02d}: "
                f"{program} {batch_start_year}-{batch_end_year} ({campus_short})"
            )
            description = (
                f"A collaborative alumni community focused on {focus_area}. "
                f"Members share job opportunities, mentorship, and project ideas "
                f"for {program} graduates from batch {batch_start_year}-{batch_end_year}. "
                f"{self.SEED_MARKER}"
            )

            group, was_created = AlumniGroup.objects.get_or_create(
                name=name,
                defaults={
                    "description": description,
                    "group_type": self.random.choices(
                        ["MANUAL", "HYBRID", "AUTO"],
                        weights=[60, 30, 10],
                        k=1,
                    )[0],
                    "visibility": self.random.choices(
                        ["PUBLIC", "PRIVATE", "RESTRICTED"],
                        weights=[70, 20, 10],
                        k=1,
                    )[0],
                    "batch_start_year": batch_start_year,
                    "batch_end_year": batch_end_year,
                    "course": program,
                    "campus": campus_code,
                    "created_by": self.random.choice(users) if users else None,
                    "is_active": True,
                    "requires_approval": self.random.choice([True, False]),
                    "has_security_questions": False,
                    "require_post_approval": self.random.choice([True, False]),
                    "max_members": self.random.choice([None, 120, 200, 300]),
                },
            )

            if was_created:
                created += 1
            else:
                existing += 1

            groups.append(group)

        return groups, {"created": created, "existing": existing}

    def _ensure_memberships(self, groups, users):
        created = 0
        existing = 0

        if not groups or not users:
            return {"created": created, "existing": existing}

        for group in groups:
            admin_user = group.created_by or self.random.choice(users)

            _, was_created = GroupMembership.objects.get_or_create(
                group=group,
                user=admin_user,
                defaults={
                    "role": "ADMIN",
                    "status": "APPROVED",
                    "is_active": True,
                },
            )
            if was_created:
                created += 1
            else:
                existing += 1

            remaining_users = [user for user in users if user.pk != admin_user.pk]
            if not remaining_users:
                continue

            target_members = min(
                len(remaining_users),
                self.random.randint(4, 12),
            )
            sampled_users = self.random.sample(remaining_users, k=target_members)

            for member in sampled_users:
                role = self.random.choices(
                    ["MEMBER", "MODERATOR"],
                    weights=[85, 15],
                    k=1,
                )[0]
                status = self.random.choices(
                    ["APPROVED", "PENDING", "REJECTED"],
                    weights=[80, 15, 5],
                    k=1,
                )[0]

                _, was_created = GroupMembership.objects.get_or_create(
                    group=group,
                    user=member,
                    defaults={
                        "role": role,
                        "status": status,
                        "is_active": True,
                    },
                )

                if was_created:
                    created += 1
                else:
                    existing += 1

        return {"created": created, "existing": existing}

    def _ensure_events(self, prefix, count, users, groups):
        created = 0
        existing = 0
        events = []

        for index in range(1, count + 1):
            theme = self.random.choice(self.EVENT_THEMES)
            title = f"{prefix} Event {index:02d}: {theme}"
            status = self.random.choices(
                ["draft", "published", "cancelled", "completed"],
                weights=[20, 55, 10, 15],
                k=1,
            )[0]
            start_date, end_date = self._build_event_window(status)

            is_virtual = self.random.random() < 0.35
            location = "Virtual Event" if is_virtual else self.random.choice(self.EVENT_VENUES)
            virtual_link = (
                f"https://meet.google.com/seed-{index:02d}-{self.random.randint(100, 999)}"
                if is_virtual
                else None
            )

            if status == "published":
                visibility = self.random.choices(
                    ["public", "private"],
                    weights=[85, 15],
                    k=1,
                )[0]
            else:
                visibility = self.random.choices(
                    ["public", "private"],
                    weights=[30, 70],
                    k=1,
                )[0]

            description = (
                f"{theme} for NORSU alumni chapters. "
                f"This session includes a keynote, open forum, and networking segment.\n\n"
                f"Expected outcomes:\n"
                f"1. Stronger alumni collaboration.\n"
                f"2. Better visibility of opportunities.\n"
                f"3. Action items for chapter leads.\n\n"
                f"{self.SEED_MARKER}"
            )

            event, was_created = Event.objects.get_or_create(
                title=title,
                defaults={
                    "description": description,
                    "start_date": start_date,
                    "end_date": end_date,
                    "location": location,
                    "is_virtual": is_virtual,
                    "virtual_link": virtual_link,
                    "max_participants": self.random.choice(
                        [None, 50, 80, 100, 150, 250]
                    ),
                    "status": status,
                    "visibility": visibility,
                    "created_by": self.random.choice(users),
                },
            )

            if was_created:
                created += 1

                # Avoid event notification signal spam on published events.
                if groups and status != "published":
                    group_count = min(len(groups), self.random.randint(0, 2))
                    if group_count > 0:
                        event.notified_groups.set(
                            self.random.sample(groups, k=group_count)
                        )
            else:
                existing += 1

            events.append(event)

        return events, {"created": created, "existing": existing}

    def _build_event_window(self, status):
        now = timezone.now()
        duration_hours = self.random.choice([2, 3, 4, 6])

        if status == "completed":
            start = now - timedelta(
                days=self.random.randint(20, 180),
                hours=self.random.randint(0, 8),
            )
        elif status == "draft":
            start = now + timedelta(
                days=self.random.randint(20, 180),
                hours=self.random.randint(0, 8),
            )
        elif status == "cancelled":
            start = now + timedelta(
                days=self.random.randint(5, 120),
                hours=self.random.randint(0, 8),
            )
        else:  # published
            start = now + timedelta(
                days=self.random.randint(-7, 120),
                hours=self.random.randint(0, 8),
            )

        end = start + timedelta(hours=duration_hours)

        # Ensure completed events end in the past.
        if status == "completed" and end > now:
            end = now - timedelta(hours=1)
            start = end - timedelta(hours=duration_hours)

        return start, end

    def _ensure_announcements(self, prefix, count, categories):
        created = 0
        existing = 0

        for index in range(1, count + 1):
            topic = self.random.choice(self.ANNOUNCEMENT_TOPICS)
            title = f"{prefix} Announcement {index:02d}: {topic}"
            posted_at = timezone.now() - timedelta(
                days=self.random.randint(0, 120),
                hours=self.random.randint(0, 23),
            )

            content = (
                f"{topic}\n\n"
                f"We are inviting all alumni to participate in this initiative. "
                f"Please review the timeline, eligibility, and submission details.\n\n"
                f"Action steps:\n"
                f"- Review requirements in the alumni portal.\n"
                f"- Coordinate with your chapter representatives.\n"
                f"- Submit before the published deadline.\n\n"
                f"{self.SEED_MARKER}"
            )

            _, was_created = Announcement.objects.get_or_create(
                title=title,
                defaults={
                    "content": content,
                    "date_posted": posted_at,
                    "priority_level": self.random.choices(
                        ["LOW", "MEDIUM", "HIGH", "URGENT"],
                        weights=[15, 55, 25, 5],
                        k=1,
                    )[0],
                    "target_audience": self.random.choices(
                        ["ALL", "RECENT", "DEPARTMENT"],
                        weights=[70, 20, 10],
                        k=1,
                    )[0],
                    "category": self.random.choice(categories),
                    "is_active": True,
                    "views_count": self.random.randint(15, 500),
                },
            )

            if was_created:
                created += 1
            else:
                existing += 1

        return {"created": created, "existing": existing}
