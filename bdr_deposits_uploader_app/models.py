import uuid

from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    """
    This extends the User object to include additional fields.

    This webapp is set up to create a UserProfile record automatically when a User record is created.
    See the README for more info about that.
    """

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    can_create_app = models.BooleanField(default=False)
    can_configure_these_apps = models.JSONField(default=list, blank=True)
    can_view_these_apps = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"{self.user.username}'s profile"


class AppConfig(models.Model):
    """
    This model represents an app that can be configured by staff.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    temp_config_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        """
        Showing full slug so it appears correctly in admin form-view.
        """
        # short_slug = self.slug if len(self.slug) <= 10 else f'{self.slug[:10]}...'
        # return short_slug
        return self.slug


class Submission(models.Model):
    """
    This model represents a user's submission of a deposit.
    """

    STATUS_CHOICES = (
        ('ready_to_ingest', 'Ready to Ingest'),
        ('ingested', 'Ingested'),  # fully ingested
        ('ingest_error', 'Ingestion Error'),
    )

    ## non-form-data ------------------------------------------------

    ## general ----------------------------------
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    app = models.ForeignKey(AppConfig, on_delete=models.CASCADE, null=True)
    student_eppn = models.CharField(max_length=255, blank=True, null=True)

    ## timestamps -------------------------------
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    ## form-data ----------------------------------------------------

    ## basics -----------------------------------
    student_email = models.CharField(max_length=255, blank=True, null=True)  # displayed but not editable
    title = models.CharField(max_length=255)
    abstract = models.TextField()
    ## collaborators ----------------------------
    advisors_and_readers = models.CharField(max_length=255, blank=True, null=True)
    team_members = models.CharField(max_length=255, blank=True, null=True)
    faculty_mentors = models.CharField(max_length=255, blank=True, null=True)
    authors = models.CharField(max_length=255, blank=True, null=True)
    ## departments/programs ---------------------
    department = models.CharField(max_length=255, blank=True, null=True)
    research_program = models.CharField(max_length=255, blank=True, null=True)
    ## access and visibility --------------------
    license_options = models.CharField(max_length=100, blank=True, null=True)
    visibility_options = models.CharField(max_length=100, blank=True, null=True)
    ## other ------------------------------------
    concentrations = models.CharField(max_length=255, blank=True, null=True)
    degrees = models.CharField(max_length=255, blank=True, null=True)
    ## file stuff -------------------------------
    primary_file = models.FileField(upload_to='primary_files/', blank=True, null=True)
    supplementary_files = models.FileField(upload_to='supplementary_files/', blank=True, null=True)  # not currently used
    original_file_name = models.CharField(max_length=255, blank=True, null=True)
    staged_file_name = models.CharField(max_length=255, blank=True, null=True)  # added field
    checksum_type = models.CharField(max_length=100, blank=True, null=True)
    checksum = models.CharField(max_length=255, blank=True, null=True)
    ## form-data --------------------------------
    temp_submission_json = models.JSONField(default=dict, blank=True)
    ## ingestion stuff --------------------------
    status = models.CharField(max_length=100, choices=STATUS_CHOICES, default='created')
    staff_ingester = models.CharField(max_length=100, blank=True, null=True)  # email address
    ingest_error_message = models.TextField(blank=True, null=True)
    bdr_pid = models.CharField(max_length=20, blank=True, null=True, verbose_name='BDR PID')
    ## (end of main fields)

    @property
    def bdr_url(self) -> str | None:
        """
        Returns the full BDR URL based on the bdr_pid, or None if not set.
        """
        if not self.bdr_pid:
            return None
        return f'{settings.BDR_PUBLIC_ITEM_ROOT_URL}{self.bdr_pid}/'

    def __str__(self):
        title_short = self.title if len(self.title) <= 10 else f'{self.title[:10]}...'
        return title_short

    ## end class Submission()
