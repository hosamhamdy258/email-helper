from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from django.shortcuts import redirect, render
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from django import forms
from django.http import JsonResponse
from django.urls import path
import re
import json
from .models import TemplateType, EmailTemplate, Recipient, CustomVariable, SentEmail, SentEmailAttachment, Position


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active',]
    list_filter = ['is_active', ]
    search_fields = ['name', 'description']
    list_editable = ['is_active']
    fields = ('name', 'description', 'is_active')


@admin.register(TemplateType)
class TemplateTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']
    list_editable = ['is_active']
    fields=  ('name', 'is_active')


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'subject', 'is_active', 'create_email_action']
    list_filter = ['template_type', 'is_active']
    search_fields = ['name', 'subject', 'body']
    list_editable = ['is_active']
    fields = ('name', 'template_type','subject', 'body', 'is_active')


    def create_email_action(self, obj):
        """Display create email button for each template"""
        url = f"/admin/emails/sentemail/add/?template={obj.id}"
        return format_html(
            '<a class="button" href="{}" style="background: #4f46e5; color: white; padding: 4px 8px; border-radius: 4px; text-decoration: none;">Create Email</a>',
            url
        )
    create_email_action.short_description = 'Actions'


@admin.register(CustomVariable)
class CustomVariableAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'default_value', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'display_name']
    list_editable = ['is_active', 'default_value']
    fields = ('name', 'display_name', 'default_value', 'is_active')





class SentEmailAttachmentInline(admin.TabularInline):
    model = SentEmailAttachment
    extra = 1
    max_num = 20
    readonly_fields = ['size_display', 'uploaded_at']
    fields = ['file', 'filename', 'size_display', 'uploaded_at']

    def size_display(self, obj):
        """Format file size"""
        if not obj.pk or not obj.size:
            return "N/A"
        if obj.size < 1024:
            return f"{obj.size} B"
        elif obj.size < 1024 * 1024:
            return f"{obj.size / 1024:.1f} KB"
        else:
            return f"{obj.size / (1024 * 1024):.1f} MB"
    size_display.short_description = 'Size'


def populate_from_template(modeladmin, request, queryset):
    """Admin action to populate sent email from template"""
    if queryset.count() == 1:
        sent_email = queryset.first()
        if sent_email.template:
            sent_email.subject = sent_email.template.subject
            sent_email.body = sent_email.template.body
            sent_email.save()
            modeladmin.message_user(
                request,
                f"Email populated from template '{sent_email.template.name}'",
                messages.SUCCESS
            )
        else:
            modeladmin.message_user(
                request,
                "Selected email has no template to populate from.",
                messages.ERROR
            )
    else:
        modeladmin.message_user(
            request,
            f"Please select exactly one email to populate. You selected {queryset.count()}.",
            messages.ERROR
        )


populate_from_template.short_description = "Populate from template"


def send_selected_emails(modeladmin, request, queryset):
    """Admin action to send selected emails"""
    sent_count = 0
    failed_count = 0
    
    for sent_email in queryset:
        if sent_email.status == 'success':
            continue  # Skip already sent emails
            
        success, error_msg = modeladmin.send_email_from_admin(sent_email)
        if success:
            sent_email.status = 'success'
            sent_email.sent_at = timezone.now()
            sent_email.error_message = ''
            sent_email.save(update_fields=['status', 'sent_at', 'error_message'])
            sent_count += 1
        else:
            sent_email.status = 'failed'
            sent_email.error_message = error_msg
            sent_email.save(update_fields=['status', 'error_message'])
            failed_count += 1
    
    if sent_count == 0:
        modeladmin.message_user(
            request,
            f"✓ All Selected recipients was sent before.",
            messages.WARNING
        )
    if sent_count > 0:
        modeladmin.message_user(
            request,
            f"✓ Successfully sent {sent_count} email(s).",
            messages.SUCCESS
        )
    if failed_count > 0:
        modeladmin.message_user(
            request,
            f"✗ Failed to send {failed_count} email(s).",
            messages.ERROR
        )


send_selected_emails.short_description = "Send selected emails"

from easy_select2 import apply_select2
class SentEmailAdminForm(forms.ModelForm):
    """Custom form for SentEmail with validation"""
    class Meta:
        widgets = {
            'recipient': apply_select2(forms.Select),
            'cc_recipients': apply_select2(forms.Select),
            'bcc_recipients': apply_select2(forms.Select),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        recipient = cleaned_data.get('recipient')
        cc_recipients = cleaned_data.get('cc_recipients')
        bcc_recipients = cleaned_data.get('bcc_recipients')

        # Check for overlaps between recipient, CC, and BCC
        errors = []

        if recipient and cc_recipients and recipient in cc_recipients:
            errors.append("The main recipient cannot also be in the CC list.")

        if recipient and bcc_recipients and recipient in bcc_recipients:
            errors.append("The main recipient cannot also be in the BCC list.")

        if cc_recipients and bcc_recipients:
            overlap = cc_recipients.intersection(bcc_recipients)
            if overlap:
                overlap_names = ', '.join([r.name for r in overlap])
                errors.append(f"The following recipients cannot be in both CC and BCC lists: {overlap_names}")

        if errors:
            raise forms.ValidationError(errors)

        return cleaned_data


@admin.register(SentEmail)
class SentEmailAdmin(admin.ModelAdmin):
    form = SentEmailAdminForm
    list_display = ['recipient', 'subject', 'status', 'sent_at', 'attachment_count']
    list_filter = ['status', 'sent_at', 'template']
    search_fields = ['recipient__name', 'recipient__email', 'subject', 'body']
    actions = [populate_from_template, send_selected_emails]
    readonly_fields = ['sent_at', 'error_message']
    inlines = [SentEmailAttachmentInline]
    fields = ('recipient', 'cc_recipients', 'bcc_recipients', 'template', 'subject',
              'body','interview_datetime','custom_variables'
              )
    


    class Media:
        js = ('admin/js/sentemail_admin.js',)

    def get_urls(self):
        """Add custom URL for template loading"""
        urls = super().get_urls()
        custom_urls = [
            path('get-template/<int:template_id>/', 
                 self.admin_site.admin_view(self.get_template_data),
                 name='emails_sentemail_get_template'),
        ]
        return custom_urls + urls

    def get_template_data(self, request, template_id):
        """AJAX endpoint to get template data"""
        try:
            template = EmailTemplate.objects.get(pk=template_id)
            return JsonResponse({
                'success': True,
                'subject': template.subject,
                'body': template.body,
            })
        except EmailTemplate.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Template not found'
            })

    def attachment_count(self, obj):
        """Display attachment count"""
        count = obj.attachments.count()
        if count > 0:
            return format_html(
                '<span style="background: #10b981; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px;">{}</span>', 
                count
            )
        return format_html('<span style="color: #6b7280;">0</span>')
    attachment_count.short_description = 'Attachments'

    def get_form(self, request, obj=None, **kwargs):
        """Customize form to populate from template when template is selected"""
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['custom_variables'].initial = dict(CustomVariable.objects.filter(is_active=True).values_list("name","default_value"))
  
        # Pre-populate from URL parameter only on new object
        if obj is None and request.method == 'GET':
            template_id = request.GET.get('template')
            if template_id:
                try:
                    template = EmailTemplate.objects.get(pk=template_id)
                    form.base_fields['subject'].initial = template.subject
                    form.base_fields['body'].initial = template.body
                    form.base_fields['template'].initial = template
                except EmailTemplate.DoesNotExist:
                    pass

        return form

    def save_model(self, request, obj, form, change):
        """Handle email sending when saving"""
        # Validate attachments before saving
        if not change:  # Only for new objects
            formset = None
            if hasattr(request, '_formsets'):
                for fs in request._formsets:
                    if fs.model == SentEmailAttachment:
                        formset = fs
                        break
            
            if formset:
                total_size = 0
                for form in formset:
                    if form.cleaned_data and not form.cleaned_data.get('DELETE'):
                        if 'file' in form.cleaned_data and form.cleaned_data['file']:
                            file_obj = form.cleaned_data['file']
                            # Check individual file size (5MB)
                            if file_obj.size > 5 * 1024 * 1024:
                                messages.error(
                                    request,
                                    f"File '{file_obj.name}' exceeds 5MB limit ({file_obj.size / (1024*1024):.1f}MB)"
                                )
                                return
                            total_size += file_obj.size
                
                # Check total size (20MB)
                if total_size > 20 * 1024 * 1024:
                    messages.error(
                        request,
                        f"Total attachment size exceeds 20MB limit ({total_size / (1024*1024):.1f}MB)"
                    )
                    return
        
        # Save the object first
        super().save_model(request, obj, form, change)
        
        # Check if we should send the email
        if '_send' in request.POST:
            success, error_msg = self.send_email_from_admin(obj)
            if success:
                obj.status = 'success'
                obj.sent_at = timezone.now()
                obj.error_message = ''
                obj.save(update_fields=['status', 'sent_at', 'error_message'])

                # Build success message with CC and BCC info
                cc_count = obj.cc_recipients.count()
                bcc_count = obj.bcc_recipients.count()

                extra_info = []
                if cc_count > 0:
                    cc_names = list(obj.cc_recipients.values_list('name', flat=True))
                    extra_info.append(f"CC: {', '.join(cc_names)}")
                if bcc_count > 0:
                    bcc_names = list(obj.bcc_recipients.values_list('name', flat=True))
                    extra_info.append(f"BCC: {', '.join(bcc_names)}")

                extra_text = f" ({'; '.join(extra_info)})" if extra_info else ""

                messages.success(
                    request, 
                    f'✓ Email sent successfully to {obj.recipient.name} ({obj.recipient.email}){extra_text}!'
                )
            else:
                obj.status = 'failed'
                obj.error_message = error_msg
                obj.save(update_fields=['status', 'error_message'])
                messages.error(request, f'✗ Failed to send email: {error_msg}')

    def save_formset(self, request, form, formset, change):
        """Save formset with file validation"""
        if formset.model == SentEmailAttachment:
            instances = formset.save(commit=False)
            for instance in instances:
                if instance.file:
                    # Auto-fill filename and metadata
                    if not instance.filename:
                        instance.filename = instance.file.name
                    if not instance.content_type:
                        instance.content_type = instance.file.file.content_type if hasattr(instance.file, 'file') else 'application/octet-stream'
                    if not instance.size:
                        instance.size = instance.file.size
                instance.save()
            formset.save_m2m()
        else:
            super().save_formset(request, form, formset, change)

    def send_email_from_admin(self, obj):
        """Send email from admin interface with full variable replacement and attachments"""
        try:
            # Build context for placeholder replacement
            context = {
                'name': obj.recipient.name,
                'email': obj.recipient.email,
                'position': obj.recipient.position.name if obj.recipient.position else 'N/A',
            }

            # Add interview date/time if provided
            if obj.interview_datetime:
                context['interview_datetime'] = obj.interview_datetime.strftime('%B %d, %Y at %I:%M %p')

            # Add custom variables from the custom_variables JSON field
            if obj.custom_variables:
                context.update(obj.custom_variables)
            
            # Replace placeholders in subject and body
            subject = obj.subject
            body = obj.body
            
            for key, value in context.items():
                placeholder = f'{{{{{key}}}}}'
                subject = subject.replace(placeholder, str(value))
                body = body.replace(placeholder, str(value))

            # Check if body contains HTML
            has_html = bool(re.search(r'<[^>]+>', body))

            if has_html:
                # Send as HTML email
                text_content = strip_tags(body)
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[obj.recipient.email],
                )
                email.attach_alternative(body, "text/html")
            else:
                # Send as plain text email
                email = EmailMessage(
                    subject=subject,
                    body=body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[obj.recipient.email],
                )

            # Add CC recipients if any
            cc_emails = list(obj.cc_recipients.values_list('email', flat=True))
            if cc_emails:
                email.cc = cc_emails
                
            # Add BCC recipients if any
            bcc_emails = list(obj.bcc_recipients.values_list('email', flat=True))
            if bcc_emails:
                email.bcc = bcc_emails

            # Attach files if any
            attachments = obj.attachments.all()
            for attachment in attachments:
                if attachment.file and hasattr(attachment.file, 'path'):
                    email.attach_file(attachment.file.path)

            # Send email
            email.send(fail_silently=False)
            return True, None

        except Exception as e:
            error_msg = str(e)
            print(f"Email sending error: {error_msg}")
            import traceback
            traceback.print_exc()
            return False, error_msg

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Add custom context to change view"""
        extra_context = extra_context or {}
        extra_context['show_save_and_send'] = True
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def add_view(self, request, form_url='', extra_context=None):
        """Add custom context to add view"""
        extra_context = extra_context or {}
        extra_context['show_save_and_send'] = True
        return super().add_view(request, form_url, extra_context=extra_context)

    def response_change(self, request, obj):
        """Handle custom button responses"""
        if '_send' in request.POST:
            return redirect(request.path)
        return super().response_change(request, obj)

    def response_add(self, request, obj, post_url_continue=None):
        """Handle custom button responses for add view"""
        if '_send' in request.POST:
            return redirect(f'/admin/emails/sentemail/{obj.pk}/change/')
        return super().response_add(request, obj, post_url_continue)


@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'position', 'email_count']
    list_filter = ['position']
    search_fields = ['name', 'email', 'notes']
    fields = ('name', 'email', 'position','notes')

    def email_count(self, obj):
        """Display count of emails sent to this recipient"""
        count = obj.sent_emails.count()
        if count > 0:
            return format_html(
                '<a href="/admin/emails/sentemail/?recipient__id__exact={}">{} emails</a>',
                obj.id, count
            )
        return '0 emails'
    email_count.short_description = 'Sent Emails'