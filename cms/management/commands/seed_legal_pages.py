from datetime import date

from django.core.management.base import BaseCommand

from cms.models import LegalPage


DEFAULT_LEGAL_PAGES = [
    {
        'page_type': 'terms',
        'title': 'Terms of Use',
        'summary': 'The rules that apply when accessing and using the NORSU Alumni Network.',
        'effective_date': date(2026, 10, 7),
        'order': 1,
        'content': """
## 1. About these terms

These Terms of Use govern access to and use of the NORSU Alumni Network operated by Negros Oriental State University through the Office of Alumni Affairs. By creating an account or using the platform, you agree to follow these terms and all applicable laws and university policies.

## 2. Eligibility and accounts

The platform is intended for NORSU alumni, authorized university personnel, and other users approved by the University. You must provide accurate information, keep your login credentials confidential, and promptly update information that is no longer correct. You are responsible for activity performed through your account unless you promptly report unauthorized access.

## 3. Permitted use

You may use the platform to maintain an alumni profile, connect with other members, participate in groups and events, access career opportunities, join mentorship activities, answer surveys, and use other services made available by the University.

You must not:

- impersonate another person or misrepresent your affiliation with NORSU;
- harass, threaten, discriminate against, or exploit another user;
- publish unlawful, misleading, defamatory, obscene, or infringing material;
- collect, scrape, sell, or disclose alumni information without authorization;
- send spam, scams, malicious files, or unsolicited commercial messages;
- interfere with the security, availability, or operation of the platform; or
- use the platform for activities unrelated to its alumni and university purposes.

## 4. Member content

You remain responsible for content you submit. You grant the University permission to store, reproduce, and display that content only as reasonably needed to operate, secure, moderate, and improve the platform. Do not upload content you do not have the right to share.

## 5. Directory, jobs, events, mentorship, and donations

Member profiles, job posts, events, mentorship information, and community content may be supplied by users or third parties. The University may review or remove content but does not guarantee every listing, opportunity, mentor, event, or statement. Exercise appropriate judgment before entering an arrangement, sharing additional information, attending an activity, or transferring funds.

## 6. Moderation and account action

The University may restrict content, suspend features, or deactivate an account when reasonably necessary to protect users, enforce these terms, comply with law, or preserve platform security. Where appropriate, affected users may contact the Office of Alumni Affairs for clarification or review.

## 7. Privacy

Personal data is handled as described in the Privacy Notice. Platform communications and user content are not a substitute for emergency, medical, legal, financial, or professional advice.

## 8. Availability and third-party services

The University may change, suspend, or discontinue features and cannot guarantee uninterrupted or error-free access. Links and integrations provided by third parties are governed by their own terms and privacy practices.

## 9. Changes to these terms

Material changes will be posted on this page and, where appropriate, communicated through the platform or registered email address. The effective date identifies the current version.

## 10. Governing law and contact

These terms are governed by the laws of the Republic of the Philippines. Questions may be submitted through the official NORSU Alumni Network contact channels shown on this website.
""".strip(),
    },
    {
        'page_type': 'privacy',
        'title': 'Privacy Notice',
        'summary': 'How NORSU collects, uses, shares, retains, and protects personal data in the Alumni Network.',
        'effective_date': date(2026, 10, 7),
        'order': 2,
        'content': """
## 1. Who is responsible for your data

Negros Oriental State University, through the Office of Alumni Affairs, operates the NORSU Alumni Network and acts as the personal information controller for personal data processed through the platform. Privacy questions and requests may be sent through the official contact details shown on this website or through the Data Privacy Request page.

## 2. Data we may collect

Depending on the services you use, the platform may process:

- account and identity information, including name, email address, authentication records, and profile photograph;
- alumni and education information, including campus, program, graduation year, achievements, and uploaded supporting documents;
- profile and contact information, including biography, birth date, gender, address, social profiles, skills, employment, position, employer, industry, and salary range;
- community activity, including connections, groups, posts, comments, direct messages, attachments, announcements, and notifications;
- event, mentorship, career, survey, and tracer-study records;
- donation information, including campaign activity, reference numbers, payment proof, verification records, and fraud-prevention signals;
- technical and security information, including IP address, device or browser information, session records, security events, and service logs; and
- information received from approved sign-in or service providers when you choose to use them.

## 3. Why we process data

We process personal data to verify and administer accounts; maintain the alumni directory; provide communication, group, event, career, mentorship, survey, donation, and support services; send requested or operational notices; protect users and the platform; produce authorized institutional reports and statistics; meet legal obligations; and improve services.

Processing is based on the applicable lawful basis, which may include consent, performance of a requested service, compliance with law, protection of legitimate interests and security, or performance of the University's lawful public and institutional functions.

## 4. Profile visibility and your choices

Some profile information may be visible to other authorized members when your profile is public. Privacy settings control supported directory visibility, but information you deliberately post in groups, messages, events, or other shared areas may be visible to their intended participants. Review your settings and avoid publishing information you do not want others to receive.

## 5. Sharing and service providers

Data may be accessed by authorized university personnel and disclosed to service providers that support hosting, email delivery, authentication, security, CAPTCHA, storage, and other platform operations. Data may also be disclosed when required by law, necessary to protect rights or safety, or directed by the data subject. Providers receive only the access reasonably needed for their role and are subject to applicable safeguards.

## 6. Retention

Records are retained only for as long as needed for the purposes described above, applicable university recordkeeping requirements, dispute resolution, security, and legal obligations. Retention periods vary by record type. Data that no longer needs to be retained will be deleted, anonymized, or securely disposed of, subject to lawful exceptions.

## 7. Security

The University applies reasonable organizational, physical, and technical safeguards appropriate to the nature of the data. No online service can guarantee absolute security. Report suspected unauthorized access or disclosure promptly through the official contact channels.

## 8. Your privacy rights

Subject to the Data Privacy Act of 2012 and applicable limitations, you may request to be informed, access your personal data, object to certain processing, correct inaccurate data, request erasure or blocking, obtain data portability where applicable, claim damages, or file a complaint. The University may verify your identity before acting on a request.

## 9. International or third-party processing

Some service providers may process data outside the Philippines. Where this occurs, the University will require appropriate contractual, organizational, and technical safeguards consistent with applicable law.

## 10. Updates and complaints

Material changes will be posted on this page and communicated when appropriate. You may contact the University through the Data Privacy Request page. You may also lodge a complaint with the National Privacy Commission.
""".strip(),
    },
    {
        'page_type': 'community-guidelines',
        'title': 'Community Guidelines',
        'summary': 'Standards for safe, respectful, and useful participation in the alumni community.',
        'effective_date': date(2026, 10, 7),
        'order': 3,
        'content': """
## Be respectful

Treat alumni, students, staff, mentors, employers, donors, and guests with professionalism. Harassment, threats, hate speech, sexual exploitation, discriminatory attacks, and repeated unwanted contact are not permitted.

## Be authentic

Use accurate identity, education, employment, event, donation, and professional information. Do not impersonate another person, create deceptive accounts, falsify credentials, or misrepresent an affiliation with NORSU.

## Protect privacy

Do not publish another person's private information, messages, documents, photographs, payment records, or contact details without authorization. Alumni directory access must not be used for scraping, mass solicitation, surveillance, or resale.

## Keep content lawful and useful

Do not post scams, spam, malware, unlawful material, infringing content, or deliberately false information. Job posts, events, fundraising campaigns, and mentorship offers must clearly describe who is responsible and must not request improper payments or sensitive credentials.

## Use reporting tools responsibly

Report content or conduct that may violate these guidelines. Do not submit knowingly false or retaliatory reports. Immediate threats or emergencies should be reported to the appropriate authorities, not only through the platform.

## Enforcement

Depending on severity and history, the University may remove content, limit features, issue a warning, suspend an account, deactivate access, preserve relevant records, or refer a matter to appropriate university offices or authorities. Users may contact the Office of Alumni Affairs to request clarification or review.
""".strip(),
    },
    {
        'page_type': 'data-privacy-request',
        'title': 'Data Privacy Request',
        'summary': 'How to exercise your data-subject rights or raise a privacy concern.',
        'effective_date': date(2026, 10, 7),
        'order': 4,
        'content': """
## Requests you may make

Subject to applicable law, you may ask to:

- confirm whether the University processes your personal data;
- access personal data associated with you;
- correct incomplete, outdated, or inaccurate information;
- object to certain processing;
- request erasure, blocking, or restriction where applicable;
- obtain portable data where the right applies; or
- report a suspected privacy violation or personal data breach.

## How to submit a request

Send your request through the official contact email or contact page shown on this website. Use the subject **Data Privacy Request** and include:

1. your full name and registered email address;
2. the right or action you want to exercise;
3. enough detail to locate the relevant records; and
4. your preferred contact method.

Do not send passwords or unnecessary identity documents by ordinary email. The University may request reasonable proof of identity through a safer channel before releasing or changing records.

## What happens next

The University will acknowledge, assess, and respond within the period required by applicable law. A request may be limited or denied when a lawful exception applies, another person's rights would be affected, records must be retained by law, or identity cannot be adequately verified. Any limitation will be explained when legally permitted.

## Complaints

If you believe your privacy concern was not adequately addressed, you may contact the NORSU Data Protection Officer through the University's official channels or file a complaint with the National Privacy Commission at [privacy.gov.ph](https://privacy.gov.ph/).
""".strip(),
    },
]


class Command(BaseCommand):
    help = 'Create missing default legal pages without overwriting admin edits'

    def handle(self, *args, **options):
        created = 0
        for page_data in DEFAULT_LEGAL_PAGES:
            page_type = page_data['page_type']
            defaults = {key: value for key, value in page_data.items() if key != 'page_type'}
            _, was_created = LegalPage.objects.get_or_create(
                page_type=page_type,
                defaults={**defaults, 'is_published': True},
            )
            created += int(was_created)

        self.stdout.write(self.style.SUCCESS(
            f'Legal pages ready: {created} created, {len(DEFAULT_LEGAL_PAGES) - created} preserved.'
        ))
        self.stdout.write(self.style.WARNING(
            'Have the NORSU Data Protection Officer or legal counsel review the default wording before production use.'
        ))
