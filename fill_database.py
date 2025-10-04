import os
import random
from datetime import timedelta

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from emails.models import (
    Position,
    TemplateType,
    EmailTemplate,
    Recipient,
    CustomVariable,
    SentEmail,
)

UserModel = get_user_model()

# Create Superuser
if not UserModel.objects.filter(username="admin").exists():
    UserModel.objects.create_superuser("admin", "admin@example.com", "admin")

# Config
NUM_POSITIONS = 5
NUM_TEMPLATE_TYPES = 4
NUM_TEMPLATES = 8
NUM_RECIPIENTS = 10
NUM_CUSTOM_VARS = 6
NUM_SENT_EMAILS = 5

# Sample data
positions = [
    "Software Engineer",
    "Product Manager",
    "Data Scientist",
    "UX Designer",
    "DevOps Engineer"
]

template_types = [
    "Initial Screening",
    "Technical Interview",
    "Final Interview",
    "Job Offer"
]

templates_data = [
    {
        "name": "Initial Screening Invitation",
        "template_type": "Initial Screening",
        "subject": "Interview Invitation - {{position}} Position at {{company_name}}",
        "body": """
        <h2>Interview Invitation</h2>
        <p>Dear {{name}},</p>
        <p>We are pleased to invite you for an initial screening interview for the {{position}} position at {{company_name}}.</p>
        <p><strong>Interview Details:</strong></p>
        <ul>
            <li><strong>Date & Time:</strong> {{interview_datetime}}</li>
            <li><strong>Location:</strong> {{interview_location}}</li>
            <li><strong>Duration:</strong> 30 minutes</li>
        </ul>
        <p>Please confirm your availability by replying to this email.</p>
        <p>Best regards,<br>{{company_name}} HR Team</p>
        """
    },
    {
        "name": "Technical Interview Schedule",
        "template_type": "Technical Interview",
        "subject": "Technical Interview Scheduled - {{position}} at {{company_name}}",
        "body": """
        <h2>Technical Interview Scheduled</h2>
        <p>Dear {{name}},</p>
        <p>Your technical interview for the {{position}} position has been scheduled.</p>
        <p><strong>Interview Details:</strong></p>
        <ul>
            <li><strong>Date & Time:</strong> {{interview_datetime}}</li>
            <li><strong>Platform:</strong> {{interview_platform}}</li>
            <li><strong>Duration:</strong> 60 minutes</li>
        </ul>
        <p>Please join the meeting 5 minutes early and have your portfolio ready if applicable.</p>
        <p>Best regards,<br>{{company_name}} Technical Team</p>
        """
    },
    {
        "name": "Final Interview Invitation",
        "template_type": "Final Interview",
        "subject": "Final Interview - {{position}} Position",
        "body": """
        <h2>Final Interview Invitation</h2>
        <p>Dear {{name}},</p>
        <p>Congratulations! You have been selected for the final interview round for the {{position}} position.</p>
        <p><strong>Final Interview Details:</strong></p>
        <ul>
            <li><strong>Date & Time:</strong> {{interview_datetime}}</li>
            <li><strong>Location:</strong> {{company_address}}</li>
            <li><strong>Duration:</strong> 90 minutes</li>
        </ul>
        <p>Please bring a copy of your resume and be prepared to discuss your experience in detail.</p>
        <p>We look forward to meeting you!</p>
        <p>Best regards,<br>{{company_name}} Hiring Team</p>
        """
    },
    {
        "name": "Job Offer Letter",
        "template_type": "Job Offer",
        "subject": "Job Offer - {{position}} Position at {{company_name}}",
        "body": """
        <h2>Job Offer</h2>
        <p>Dear {{name}},</p>
        <p>We are delighted to extend a job offer for the {{position}} position at {{company_name}}.</p>
        <p><strong>Offer Details:</strong></p>
        <ul>
            <li><strong>Position:</strong> {{position}}</li>
            <li><strong>Salary:</strong> {{salary}}</li>
            <li><strong>Start Date:</strong> {{start_date}}</li>
            <li><strong>Benefits:</strong> {{benefits_summary}}</li>
        </ul>
        <p>Please review the attached offer letter and let us know your decision by {{response_deadline}}.</p>
        <p>We look forward to welcoming you to our team!</p>
        <p>Best regards,<br>{{company_name}} HR Team</p>
        """
    }
]

custom_variables_data = [
    {"name": "company_name", "display_name": "Company Name", "default_value": "Hossam Hamdy Inc."},
    {"name": "company_address", "display_name": "Company Address", "default_value": "123 Business St, Tech City"},
    {"name": "interview_location", "display_name": "Interview Location", "default_value": "Conference Room A"},
    {"name": "interview_platform", "display_name": "Interview Platform", "default_value": "Zoom Meeting"},
    {"name": "salary", "display_name": "Salary", "default_value": "$85,000 annually"},
    {"name": "benefits_summary", "display_name": "Benefits Summary", "default_value": "Health, Dental"},
    {"name": "start_date", "display_name": "Start Date", "default_value": "January 15, 2026"},
    {"name": "response_deadline", "display_name": "Response Deadline", "default_value": "December 30, 2026"},
]

# 1) Create Positions
existing_positions = set(Position.objects.values_list("name", flat=True))
for position_name in positions:
    if position_name not in existing_positions:
        Position.objects.create(name=position_name, description=f"Description for {position_name}")

# 2) Create Template Types
existing_template_types = set(TemplateType.objects.values_list("name", flat=True))
for tt_name in template_types:
    if tt_name not in existing_template_types:
        TemplateType.objects.create(name=tt_name)

# 3) Create Custom Variables
existing_custom_vars = set(CustomVariable.objects.values_list("name", flat=True))
for cv_data in custom_variables_data:
    if cv_data["name"] not in existing_custom_vars:
        CustomVariable.objects.create(
            name=cv_data["name"],
            display_name=cv_data["display_name"],
            default_value=cv_data["default_value"]
        )

# 4) Create Recipients
existing_recipients = set(Recipient.objects.values_list("email", flat=True))
sample_recipients = [
    {"name": "John Doe", "email": "john.doe@example.com", "position": "Software Engineer"},
    {"name": "Jane Smith", "email": "jane.smith@example.com", "position": "Product Manager"},
    {"name": "Mike Johnson", "email": "mike.johnson@example.com", "position": "Data Scientist"},
    {"name": "Sarah Wilson", "email": "sarah.wilson@example.com", "position": "UX Designer"},
    {"name": "David Brown", "email": "david.brown@example.com", "position": "DevOps Engineer"},
    {"name": "Lisa Davis", "email": "lisa.davis@example.com", "position": "Software Engineer"},
    {"name": "Tom Anderson", "email": "tom.anderson@example.com", "position": "Product Manager"},
    {"name": "Emily Taylor", "email": "emily.taylor@example.com", "position": "Data Scientist"},
    {"name": "Chris Martinez", "email": "chris.martinez@example.com", "position": "UX Designer"},
    {"name": "Amanda White", "email": "amanda.white@example.com", "position": "DevOps Engineer"},
]

for recipient_data in sample_recipients:
    if recipient_data["email"] not in existing_recipients:
        position = Position.objects.filter(name=recipient_data["position"]).first()
        Recipient.objects.create(
            name=recipient_data["name"],
            email=recipient_data["email"],
            position=position,
            notes=f"Applied for {recipient_data['position']} position"
        )

# 5) Create Email Templates
existing_templates = set(EmailTemplate.objects.values_list("name", flat=True))
for template_data in templates_data:
    if template_data["name"] not in existing_templates:
        template_type = TemplateType.objects.get(name=template_data["template_type"])
        EmailTemplate.objects.create(
            name=template_data["name"],
            template_type=template_type,
            subject=template_data["subject"],
            body=template_data["body"]
        )

# 6) Create Sample Sent Emails
existing_sent_emails = set(SentEmail.objects.values_list("recipient__email", "subject"))
sample_subjects = [
    "Interview Scheduled - Software Engineer Position",
    "Technical Interview Invitation - Product Manager",
    "Final Round Interview - Data Scientist",
    "Job Offer - UX Designer Position",
    "Follow-up Interview - DevOps Engineer"
]

for i in range(NUM_SENT_EMAILS):
    # Get random recipient
    recipients = list(Recipient.objects.all())
    if not recipients:
        break

    recipient = random.choice(recipients)
    subject = random.choice(sample_subjects)

    if (recipient.email, subject) not in existing_sent_emails:
        # Create sent email with sample data
        sent_email = SentEmail.objects.create(
            recipient=recipient,
            subject=subject,
            body=f"<p>This is a sample email body for {recipient.name}. Interview details would be included here.</p>",
            interview_datetime=timezone.now() + timedelta(days=random.randint(1, 14)),
            status=random.choice(['success', 'pending', 'failed']),
            custom_variables={
                "company_name": "HH Inc.",
                "interview_location": "Conference Room A",
                "company_address": "123 Business St, Tech City"
            }
        )

        # Add random CC recipients (1-2)
        cc_count = random.randint(1, 2)
        if cc_count > 0:
            other_recipients = [r for r in recipients if r != recipient]
            cc_recipients = random.sample(other_recipients, min(cc_count, len(other_recipients)))
            sent_email.cc_recipients.set(cc_recipients)

        # Add random BCC recipients (0-1)
        bcc_count = random.randint(0, 1)
        if bcc_count > 0:
            other_recipients = [r for r in recipients if r not in cc_recipients and r != recipient]
            if other_recipients:
                bcc_recipients = random.sample(other_recipients, min(bcc_count, len(other_recipients)))
                sent_email.bcc_recipients.set(bcc_recipients)

print("Database population script finished.")
print(f"Created sample data for Interview Email Manager:")
print(f"- Positions: {Position.objects.count()}")
print(f"- Template Types: {TemplateType.objects.count()}")
print(f"- Email Templates: {EmailTemplate.objects.count()}")
print(f"- Recipients: {Recipient.objects.count()}")
print(f"- Custom Variables: {CustomVariable.objects.count()}")
print(f"- Sent Emails: {SentEmail.objects.count()}")
print(f"- Superuser: admin/admin")
