# Email Notifications System - CKAN Issues Extension

This document outlines all email notification scenarios in the CKAN Issues extension, including triggers, recipients, templates, and flows.

## Configuration

Email notifications are controlled by the following configuration setting:

```ini
ckanext.issues.send_email_notifications = true
```

When set to `true`, the system will send email notifications for specific issue-related events.

## Email Notification Scenarios

### 1. New Issue Created

**Trigger:** When a user creates a new issue on a dataset

**Flow:**
1. User submits a new issue via web interface or API
2. Issue is saved to database with auto-generated issue number
3. System checks if `ckanext.issues.send_email_notifications = true`
4. If enabled, system identifies recipients using `_get_recipients()` function
5. Email is sent to each recipient using the new issue template

**Recipients:**
- All organization members with roles that have `update_dataset` permission
- Typically includes: **Admins** and **Editors** of the dataset's organization
- Recipients are determined by checking organization membership and permissions

**Email Subject Format:**
```
[{site_title} Issue] {dataset_title}
```
Example: `[NHS Data Portal Issue] Hospital Capacity Dataset`

**Template Used:** `src/ckanext-issues/ckanext/issues/templates/issues/email/new_issue.html`

**Template Variables:**
- `site_title`: Site name (e.g., "NHS Data Portal")
- `recipient.organization_title`: Organization name
- `recipient.capacity`: User's role (Admin/Editor)
- `dataset.title`: Dataset name
- `issue_subject`: Issue title
- `issue.description`: Issue description
- `user.fullname` or `user.name`: Issue creator's name
- Links to issue and dataset pages

**Email Content Example:**
```
---

On NHS Data Portal a user has raised an issue with one of the datasets from organization 'NHS Trust', for which you are an Admin.

The dataset is: Hospital Capacity Dataset
The issue is:

> Data is missing for March 2024
> The CSV file seems to be corrupted and shows no data for the entire month of March.

Please correct the problem or add an initial comment about the issue at: [issue_link]. Once the issue has been resolved, click 'Close issue'.

Thank you,

The NHS Data Portal team

--

Issue: [issue_link]
Dataset: [dataset_link]
User: John Smith
```

---

### 2. New Comment Added to Issue

**Trigger:** When a user adds a comment to an existing issue

**Flow:**
1. User submits a comment on an issue via web interface or API
2. Comment is saved to database and linked to the issue
3. System checks if `ckanext.issues.send_email_notifications = true`
4. If enabled, system identifies recipients using `_get_recipients()` function
5. Email is sent to each recipient using the new comment template

**Recipients:**
- All organization members with roles that have `update_dataset` permission
- Typically includes: **Admins** and **Editors** of the dataset's organization
- Same recipient logic as new issues

**Email Subject Format:**
```
[{site_title} Issue] {dataset_title}
```
Example: `[NHS Data Portal Issue] Hospital Capacity Dataset`

**Template Used:** `src/ckanext-issues/ckanext/issues/templates/issues/email/new_comment.html`

**Template Variables:**
- `user.fullname` or `user.name`: Comment author's name
- `site_title`: Site name
- `dataset.title`: Dataset name
- `issue_subject`: Original issue title
- `comment.comment`: The comment text
- `issue.number`: Issue number
- Links to issue and dataset pages

**Email Content Example:**
```
A user 'Jane Doe' has added a comment to one of your discussions on NHS Data Portal.

The dataset is: Hospital Capacity Dataset
The discussion is: Data is missing for March 2024
The comment is:

> I've checked the source system and confirmed that the data export failed on March 1st. 
> We're working on fixing this and will update the dataset within 48 hours.

In order to respond to the comment, please see the discussion at: [issue_link]. Once the discussion has been resolved, click 'Close discussion'.

Thank you,

The NHS Data Portal team

--

Discussion: [issue_link]
Dataset: [dataset_link]
```

---

### 3. Dataset Report Submitted

**Trigger:** When a user reports an issue with a dataset using the report form

**Flow:**
1. User visits a dataset page and finds the "Report Dataset" form
2. User fills out issue type, description, and optional email address
3. User completes reCAPTCHA verification to prevent spam
4. Form is submitted and validated
5. Email is sent to designated administrators

**Recipients:**
- **System administrators** specified in configuration
- Single email address configured in: `ckanext.nhs.dataset_report_email_to`

**Email Subject:**
```
A new issue has been reported on the Open Data Portal
```

**Template Used:** `emails/report_dataset.html`

**Email Content Includes:**
- Dataset title and link
- Issue type (from dropdown selection)
- Issue description (user's detailed report)
- Reporter's email (if provided)
- Site information

**Email Content Example:**
```
The following issue related to Hospital Capacity Dataset on the ODP has been reported:

Issue type:
Data Quality Issue

Issue description:
The data appears to be missing entries for March 2024. Several hospitals show no capacity data during this period.

Reporter email:
user@example.com

[Review dataset] (button linking to dataset)

Message sent from NHS Data Portal (https://data.nhs.uk)
```

**Configuration Required:**
```ini
ckanext.nhs.dataset_report_email_to = admin@yoursite.com
```

---

### 4. Activity Stream Notifications

**Trigger:** Scheduled email digest of recent activities on datasets/organizations the user follows

**Flow:**
1. CKAN's built-in notification system runs periodically (via cron job or manual trigger)
2. System checks each user's dashboard activity since last email was sent
3. Filters out user's own activities (users don't get notified of their own actions)
4. Groups multiple activities into a single digest email
5. Uses NHS-specific email template (patched into CKAN core)
6. Sends digest email to users who have email notifications enabled

**Recipients:**
- **Individual users** who have enabled activity stream email notifications
- Only users with `activity_streams_email_notifications = true` in their profile
- Must have valid email address in their profile

**Email Subject:**
```
{n} new activity from {site_title}
{n} new activities from {site_title}
```
(Subject varies based on number of activities - singular/plural)

**Template Used:** `activity_streams/activity_stream_email_resource_notifications.html`

**Email Content Example:**
```
You have {n} new activities in your dashboard:

• Dataset "Hospital Capacity Data" was updated by John Smith
• New resource added to "COVID-19 Statistics" by Jane Doe
• Organization "NHS Trust London" created new dataset

[View your dashboard] (button linking to user dashboard)

Message sent from NHS Data Portal (https://data.nhs.uk)
```

**Configuration Required:**
```ini
# Enable activity stream email notifications globally
ckan.activity_streams_email_notifications = true

# Set how far back to look for activities (default: 2 days)
ckan.email_notifications_since = 2

# Users must also enable it individually in their profile
```

**Timing:**
- Triggered manually via: `ckan notify send_emails` command
- Or scheduled via cron job (typically daily/weekly)
- Only sends activities since last email was sent to each user
- Respects `ckan.email_notifications_since` setting (won't send very old activities)

---


## Recipient Determination Logic

The `_get_recipients()` function determines who receives notifications:

1. **Organization Check:** Finds the organization that owns the dataset
2. **Role Check:** Gets all roles that have `update_dataset` permission
3. **Member List:** For each qualifying role, gets all organization members
4. **Recipient Object:** Creates recipient objects with:
   - `user_id`: User's ID
   - `capacity`: User's role (Admin, Editor, etc.)
   - `organization_name`: Organization name
   - `organization_title`: Organization display title

**Typical Recipients:**
- Organization **Admins**
- Organization **Editors**
- Any custom roles with `update_dataset` permission

**Not Included:**
- Organization **Members** (read-only access)
- Users outside the organization
- The user who created the issue/comment (they don't get notified of their own actions)

**Dataset Report Recipients:**
- Single configured administrator email address
- Specified in `ckanext.nhs.dataset_report_email_to` configuration

---
