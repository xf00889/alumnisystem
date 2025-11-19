# Screenshots_note

## Overview

This document outlines the screenshots needed for the Profile Management documentation. Screenshots should be added to the appropriate subdirectories under `docs/user-guide/screenshots/user-features/profile-management/`.

## Required Screenshot Directories

Create the following directories for screenshots:

```
docs/user-guide/screenshots/user-features/profile-management/
├── personal-information/
├── education-history/
├── work-experience/
├── skills/
├── documents/
└── profile-photo/
```

## Personal Information Screenshots

**Directory**: `personal-information/`

1. `profile-edit-page.png` - Main profile edit page showing all sections
2. `basic-information-form.png` - Basic information fields (name, birth date, gender, bio)
3. `contact-information-form.png` - Contact information fields (phone, social media)
4. `location-information-form.png` - Location fields (address, city, state, country)
5. `professional-information-form.png` - Professional fields (position, employer, industry)
6. `privacy-settings.png` - Privacy settings section
7. `save-success-message.png` - Success message after saving changes

## Education History Screenshots

**Directory**: `education-history/`

1. `education-section.png` - Education section with existing entries
2. `add-education-form.png` - Form for adding new education entry
3. `program-dropdown.png` - Program selection dropdown
4. `campus-dropdown.png` - Campus selection dropdown
5. `primary-education-checkbox.png` - Primary education checkbox
6. `education-entry-display.png` - How education entries appear on profile
7. `edit-education-form.png` - Form for editing existing education
8. `delete-education-confirmation.png` - Confirmation dialog for deletion

## Work Experience Screenshots

**Directory**: `work-experience/`

1. `experience-section.png` - Work experience section with entries
2. `add-experience-form.png` - Form for adding new experience
3. `current-position-checkbox.png` - "I currently work here" checkbox
4. `career-significance-dropdown.png` - Career significance options
5. `experience-with-dates.png` - Experience entry showing date ranges
6. `current-position-badge.png` - How current position is highlighted
7. `edit-experience-form.png` - Form for editing experience
8. `delete-experience-confirmation.png` - Confirmation dialog for deletion

## Skills Screenshots

**Directory**: `skills/`

1. `skills-section.png` - Skills section with existing skills
2. `add-skill-form.png` - Form for adding new skill
3. `skill-type-dropdown.png` - Skill type selection dropdown
4. `proficiency-level-dropdown.png` - Proficiency level options
5. `primary-skill-checkbox.png` - Primary skill checkbox
6. `skills-by-type-display.png` - How skills are grouped by type on profile
7. `edit-skill-form.png` - Form for editing skill
8. `delete-skill-confirmation.png` - Confirmation dialog for deletion

## Documents Screenshots

**Directory**: `documents/`

1. `documents-section.png` - Documents section overview
2. `transcript-upload-form.png` - Transcript upload form
3. `certificate-upload-form.png` - Certificate upload form
4. `diploma-upload-form.png` - Diploma upload form
5. `resume-upload-form.png` - Resume upload form
6. `file-selection-dialog.png` - File browser for selecting documents
7. `upload-progress.png` - Upload progress indicator
8. `uploaded-documents-list.png` - List of uploaded documents
9. `document-verification-badge.png` - Verified document badge
10. `delete-document-confirmation.png` - Confirmation dialog for deletion

## Profile Photo Screenshots

**Directory**: `profile-photo/`

1. `profile-photo-section.png` - Profile photo section in edit mode
2. `choose-file-button.png` - File selection button
3. `photo-preview.png` - Photo preview before saving
4. `photo-upload-success.png` - Success message after upload
5. `profile-with-photo.png` - Profile page showing uploaded photo
6. `remove-photo-option.png` - Remove photo checkbox/button
7. `default-avatar.png` - Default avatar when no photo is uploaded
8. `photo-in-navigation.png` - How photo appears in navigation bar

## Screenshot Guidelines

### Technical Requirements
- **Format**: PNG (preferred) or JPG
- **Resolution**: At least 1920x1080 for desktop screenshots
- **File Size**: Compress to under 500KB per image
- **Naming**: Use descriptive kebab-case names

### Content Guidelines
- Use sample/test data (no real personal information)
- Ensure UI is clean and professional
- Capture relevant portions of the screen
- Include context (navigation, headers) when helpful
- Highlight important elements with arrows or boxes if needed

### Privacy Guidelines
- Do not include real names, emails, or phone numbers
- Use placeholder data (e.g., "John Doe", "john.doe@example.com")
- Blur or redact any sensitive information
- Use generic company names and locations

## Adding Screenshots to Documentation

When screenshots are ready, update the documentation files to reference them:

```markdown
![Description of screenshot](../../../screenshots/user-features/profile-management/[subdirectory]/[filename].png)
```

Example:
```markdown
![Profile edit page showing all sections](../../../screenshots/user-features/profile-management/personal-information/profile-edit-page.png)
```

## Status

- [ ] Personal Information screenshots
- [ ] Education History screenshots
- [ ] Work Experience screenshots
- [ ] Skills screenshots
- [ ] Documents screenshots
- [ ] Profile Photo screenshots

---

*Last Updated: November 19, 2025*
