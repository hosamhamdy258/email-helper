from django.db import models
from django.utils import timezone
from froala_editor.fields import FroalaField

class BaseModel(models.Model):
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True

class Position(BaseModel):
    """Job positions/roles that can be assigned to recipients"""
    name = models.CharField(max_length=200, unique=True, help_text="Position name (e.g., 'Software Engineer', 'Product Manager')")
    description = models.TextField(blank=True, help_text="Description of this position")


    class Meta:
        verbose_name = 'Position'
        verbose_name_plural = 'Positions'

    def __str__(self):
        return self.name


class TemplateType(BaseModel):
    """Dynamic template types/categories"""
    name = models.CharField(max_length=100, unique=True, help_text="Template type name (e.g., '1st Interview', 'Job Offer')")

    
    class Meta:
        verbose_name = 'Template Type'
        verbose_name_plural = 'Template Types'
    
    def __str__(self):
        return self.name


class EmailTemplate(BaseModel):
    """Email template for different interview stages"""
    name = models.CharField(max_length=200, help_text="Template name for internal use")
    template_type = models.ForeignKey(TemplateType, on_delete=models.PROTECT, related_name='templates', help_text="Category of this template")
    subject = models.CharField(max_length=300, help_text="Email subject line (supports placeholders)")
    body = FroalaField(help_text="Email body with rich text formatting.\
        Use {{name}}, {{email}}, {{position}}, {{interview_date}}, {{interview_time}}, or any custom variables you've created")

    

    def __str__(self):
        return f"{self.name} ({self.template_type.name})"


class Recipient(BaseModel):
    """Candidate/Recipient information"""
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True, help_text="Position/role applied for")
    notes = models.TextField(blank=True)




    def __str__(self):
        if self.position:
            return f"{self.name} ({self.email}) - {self.position.name}"
        return f"{self.name} ({self.email})"


class CustomVariable(BaseModel):
    """Custom variables/placeholders for email templates"""
    name = models.CharField(max_length=100, unique=True, help_text="Variable name (e.g., 'company_name', 'interview_location')")
    display_name = models.CharField(max_length=150, help_text="Display name for the variable")
    default_value = models.CharField(max_length=500, blank=True, help_text="Default value if not provided")

    
    class Meta:
        verbose_name = 'Custom Variable'
        verbose_name_plural = 'Custom Variables'
    
    def __str__(self):
        return f"{{{{{self.name}}}}} - {self.display_name}"
    
    @property
    def placeholder(self):
        """Return the placeholder format"""
        return f"{{{{{self.name}}}}}"


class SentEmailAttachment(BaseModel):
    """Individual attachment for sent emails"""
    sent_email = models.ForeignKey('SentEmail', on_delete=models.CASCADE, related_name='attachments')
    # ! TODO field validation for size
    file = models.FileField(upload_to='email_attachments/')
    filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    size = models.PositiveBigIntegerField()  # Size in bytes
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.filename} ({self.sent_email})"


class SentEmail(BaseModel):
    """Track sent emails"""
    recipient = models.ForeignKey(Recipient, on_delete=models.CASCADE, related_name='sent_emails')
    cc_recipients = models.ManyToManyField(Recipient, blank=True, related_name='cc_sent_emails', help_text="CC recipients (visible to all recipients)")
    bcc_recipients = models.ManyToManyField(Recipient, blank=True, related_name='bcc_sent_emails', help_text="BCC recipients (not visible to main recipient)")
    template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    subject = models.CharField(max_length=300)
    body = FroalaField()
    interview_datetime = models.DateTimeField(null=True, blank=True, help_text="Interview date and time (optional)")
    custom_variables = models.JSONField(default=dict, blank=True, help_text="Custom variable values used in this email")
    sent_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=[
        ('success', 'Success'),
        ('pending', 'Pending'),
        ('failed', 'Failed'),
    ], default='pending')
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"Email to {self.recipient.name} - {self.sent_at.strftime('%Y-%m-%d %H:%M')}"

    def save_attachments(self, files):
        """Save multiple attachments for this email"""
        for file_obj in files:
            SentEmailAttachment.objects.create(
                sent_email=self,
                file=file_obj,
                filename=file_obj.name,
                content_type=file_obj.content_type,
                size=file_obj.size
            )
