# Interview Email Manager

A Quick and easy Django-based email management system designed for efficiently manage sending personalized emails.

## Features

### Core Functionality

- **Multi-Recipient Emailing**: Send personalized emails to multiple recipients simultaneously
- **Template System**: Create and manage reusable email templates with dynamic placeholders
- **CC/BCC Support**: Full Carbon Copy and Blind Carbon Copy functionality
- **Interview Scheduling**: Integrated date/time management for interview coordination
- **File Attachments**: Support for email attachments with size validation
- **Status Tracking**: Real-time tracking of email delivery status (Success/Pending/Failed)
- **Custom Variables**: Define and use custom placeholders in email templates
- **Rich Text Editor**: Froala editor integration for beautiful email content

## Prerequisites

- Docker & Docker Compose
- Git

## Quick Start (Docker)

### 1. Clone the Repository

```bash
git clone https://github.com/hosamhamdy258/email-helper.git
cd email-helper
```

### 3. Build and Run with Docker

```bash
# Build the Docker image
docker compose build

# Run the application
docker compose up -d

# Populate sample data (optional it's already executed when build image 1st time)
docker compose exec web python fill_database.py
```

### 4. Access the Application

- **Django Admin**: http://localhost:8000/admin/
- **Default Superuser**: admin / admin

## Email Configuration

add email configuration to start sending emails : http://localhost:8000/admin/des/dynamicemailconfiguration/

## Usage Guide

### 1. Access Django Admin

Navigate to `http://localhost:8000/admin/` and login with your superuser credentials.

### 2. Manage Recipients

- **Recipients**: Add/edit candidate information
- **Positions**: Define available job positions
- **Template Types**: Categorize your email templates

### 3. Create Email Templates

- **Template Types**: Initial Screening, Technical Interview, Final Interview, Job Offer
- **Dynamic Placeholders**:
  - `{{name}}` - Recipient's name
  - `{{email}}` - Recipient's email
  - `{{position}}` - Job position
  - `{{interview_datetime}}` - Interview date and time
  - `{{company_name}}` - Your company name

### 4. Send Emails

- **Single Recipient**: Select one recipient for targeted communication
- **Multiple Recipients**:
  - **CC (Carbon Copy)**: Visible to all recipients
  - **BCC (Blind Carbon Copy)**: Hidden from other recipients
- **Attachments**: Upload files up to 20MB total
- **Scheduling**: Set interview date/time for automatic inclusion

### 5. Track Email Status

- **Success**: Email delivered successfully
- **Pending**: Email queued for sending
- **Failed**: Email delivery failed (check error logs)

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
