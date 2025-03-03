# models.py - Updated models with document processing and loan application models

import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.exceptions import ValidationError
from mptt.models import MPTTModel, TreeForeignKey

# ===================
# Core Models
# ===================

class Application(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    version = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Client(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    legal_name = models.CharField(max_length=255, unique=True)
    short_name = models.CharField(max_length=255, unique=True)
    legal_structure = models.CharField(max_length=100, blank=True, null=True)
    fein = models.CharField(max_length=50, unique=True, blank=True, null=True)
    company_logo = models.BinaryField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    website = models.URLField(max_length=255, blank=True, null=True)
    industry = models.CharField(max_length=100, blank=True, null=True)
    year_established = models.IntegerField(blank=True, null=True)
    number_of_employees = models.IntegerField(blank=True, null=True)
    annual_revenue = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    primary_contact_name = models.CharField(max_length=255, blank=True, null=True)
    primary_contact_email = models.EmailField(max_length=255, blank=True, null=True)
    primary_contact_phone = models.CharField(max_length=20, blank=True, null=True)
    status = models.CharField(max_length=50, default='Active')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('CustomUser', related_name='created_clients', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey('CustomUser', related_name='updated_clients', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.legal_name


class Role(models.Model):
    """Role model that extends Django's group functionality"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    group = models.OneToOneField(Group, on_delete=models.CASCADE, related_name='extended_role')
    description = models.TextField(blank=True)
    application = models.ForeignKey(Application, on_delete=models.CASCADE, null=True)
    
    def __str__(self):
        return self.name


class FundingInstitution(models.Model):
    """Represents different funding institutions that can be selected"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    logo_url = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name


class CustomUser(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    middle_name = models.CharField(max_length=255, blank=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    selected_institution = models.ForeignKey(FundingInstitution, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Add related_name to fix the clash
    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        related_name='custom_user_set',
        related_query_name='custom_user'
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        related_name='custom_user_set',
        related_query_name='custom_user'
    )

    def get_accessible_menus(self):
        if not self.role:
            return Menu.objects.none()
        
        # Get all menus accessible to the user's role through MenuRole
        return Menu.objects.filter(menurole__role=self.role)
    
    class Meta:
        permissions = [
            ("can_access_admin", "Can access admin interface"),
        ]


# ===================
# Menu System Models
# ===================

class Menu(MPTTModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    path = models.CharField(max_length=255, null=True, blank=True)
    order = models.IntegerField(default=0)
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    funding_institution = models.ForeignKey(FundingInstitution, on_delete=models.CASCADE, null=True, blank=True)
    # MPTT specific fields with defaults
    level = models.PositiveIntegerField(default=0)
    lft = models.PositiveIntegerField(default=0)
    rght = models.PositiveIntegerField(default=0)
    tree_id = models.PositiveIntegerField(default=0)

    class MPTTMeta:
        order_insertion_by = ['order', 'name']

    class Meta:
        unique_together = ['application', 'name', 'funding_institution']
        permissions = [
            ("can_assign_menu", "Can assign menu to groups"),
        ]

    def clean(self):
        if self.parent and self.parent.application != self.application:
            raise ValidationError("Parent menu must belong to the same application")

    def __str__(self):
        return f"{self.application.name} - {self.name}"

    def get_admin_tree_title(self):
        return f"{self.name} ({self.path or 'No path'})"


class MenuRole(models.Model):
    """Links menus to roles with specific access levels"""
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    can_view = models.BooleanField(default=True)
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['menu', 'role']
    
    def __str__(self):
        return f"{self.role.name} - {self.menu.name}"


class MenuPermission(models.Model):
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    class Meta:
        unique_together = ['menu', 'group', 'permission']
        verbose_name = "Menu Permission Assignment"
        verbose_name_plural = "Menu Permission Assignments"


# ===================
# Document Management
# ===================

class DocumentCategory(models.Model):
    """Document categories for loan application documents"""
    PREDEFINED_CATEGORIES = [
        ('identification', 'Identification Documents'),
        ('income', 'Income Verification'),
        ('asset', 'Asset Documentation'),
        ('credit', 'Credit History'),
        ('property', 'Property Information'),
        ('debt', 'Debt Obligations'),
        ('down_payment', 'Down Payment Verification'),
        ('loan_specific', 'Loan-Specific Requirements'),
        ('additional', 'Additional Documentation'),
        ('untagged', 'Untagged'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category_seq = models.CharField(max_length=50, blank=True, null=True)
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    category_name = models.CharField(max_length=255)
    category_code = models.CharField(max_length=50, choices=PREDEFINED_CATEGORIES)
    description = models.TextField(blank=True, null=True)
    order = models.IntegerField(default=0)

    class Meta:
        unique_together = ['application', 'category_code']
        verbose_name_plural = 'Document Categories'

    def __str__(self):
        return self.category_name


class DocumentType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(DocumentCategory, on_delete=models.CASCADE, related_name='document_types')
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    type_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    is_required = models.BooleanField(default=False)
    validation_rules = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['category', 'type_name']

    def __str__(self):
        return self.type_name


class TempDocument(models.Model):
    """Temporary document storage for uploads before AI processing"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    document_name = models.CharField(max_length=255)
    document_type = models.CharField(max_length=100)
    status = models.CharField(max_length=50, default='pending')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    document_path = models.CharField(max_length=255, null=True, blank=True)
    
    def __str__(self):
        return f"{self.document_name} - {self.status}"


# ===================
# Loan Application Models
# ===================

class LoanApplication(models.Model):
    """Loan application model"""
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('UNDER_REVIEW', 'Under Review'),
        ('UNDERWRITER', 'Underwriter'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    loan_amount = models.DecimalField(max_digits=15, decimal_places=2)
    loan_purpose = models.CharField(max_length=255)
    loan_term = models.IntegerField()
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    rate_expiry_date = models.DateTimeField(blank=True, null=True)
    application_status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    submission_date = models.DateTimeField(blank=True, null=True)
    decision_date = models.DateTimeField(blank=True, null=True)
    credit_score = models.IntegerField(blank=True, null=True)
    dti_ratio = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)  # Debt-to-Income ratio
    case_readiness = models.IntegerField(default=0, help_text="Percentage completion of required documents")
    document_index = models.IntegerField(default=0, help_text="Percentage of document review completion")
    applicant_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(blank=True, null=True, default=dict)


    def __str__(self):
        return f"{self.applicant_name} - ${self.loan_amount} - {self.get_application_status_display()}"


class DocumentStage(models.Model):
    """Document storage after AI processing"""
    SOURCE_CHOICES = [
        ('MANUAL', 'Manual'),
        ('API', 'API'),
        ('BATCH', 'Batch'),
        ('EMAIL', 'Email'),
        ('SCANNER', 'Scanner'),
        ('SFTP', 'SFTP'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    loan_application = models.ForeignKey(LoanApplication, on_delete=models.CASCADE)
    category = models.ForeignKey(DocumentCategory, on_delete=models.CASCADE)
    document_name = models.CharField(max_length=255)
    document_type = models.CharField(max_length=100)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(blank=True, null=True)
    document_path = models.CharField(max_length=500, blank=True, null=True)
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='MANUAL')
    ai_confidence = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    ai_processing_details = models.JSONField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.document_name} - {self.status}"


class DocumentProcessingLog(models.Model):
    """Logs for document processing"""
    STATUS_CHOICES = [
        ('STARTED', 'Started'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(DocumentStage, on_delete=models.CASCADE)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    message = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.document.document_name} - {self.status}"


class DocumentVersion(models.Model):
    """Document versions for tracking changes"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(DocumentStage, on_delete=models.CASCADE)
    version_number = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    content = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.document.document_name} - v{self.version_number}"


class DocumentAccessLog(models.Model):
    """Logs for document access"""
    ACTION_CHOICES = [
        ('VIEWED', 'Viewed'),
        ('DOWNLOADED', 'Downloaded'),
        ('SHARED', 'Shared'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(DocumentStage, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.document.document_name} - {self.action} by {self.user.username}"


class LoanSummary(models.Model):
    """Loan summary information"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    loan_application = models.ForeignKey(LoanApplication, on_delete=models.CASCADE)
    total_loan_amount = models.DecimalField(max_digits=15, decimal_places=2)
    approved_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    annual_percentage_rate = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    monthly_payment = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    total_payment_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    loan_term_months = models.IntegerField(blank=True, null=True)
    approval_date = models.DateTimeField(blank=True, null=True)
    first_payment_date = models.DateField(blank=True, null=True)
    last_payment_date = models.DateField(blank=True, null=True)
    integration_status = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Loan summaries'

    def __str__(self):
        return f"Summary for {self.loan_application.id}"