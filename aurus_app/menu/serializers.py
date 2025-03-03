from rest_framework import serializers
from .models import TempDocument

class TempDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TempDocument
        fields = '__all__'
        read_only_fields = ('id', 'user', 'client', 'application', 'status', 'uploaded_at', 'processed_at')


from rest_framework import serializers
from .models import Menu, Role, MenuRole

class MenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = Menu
        fields = ['id', 'name', 'path', 'order', 'description']

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'description']

class MenuRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuRole
        fields = ['id', 'menu', 'role', 'can_view', 'can_edit', 'can_delete']


# serializers.py
from rest_framework import serializers
from .models import (
    CustomUser, Application, Client, DocumentCategory, DocumentType,
    TempDocument, DocumentStage, DocumentProcessingLog, LoanApplication
)

class CustomUserSerializer(serializers.ModelSerializer):
    """Serializer for user information"""
    role_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'role_name']
        read_only_fields = ['id', 'username', 'email', 'role', 'role_name']
    
    def get_role_name(self, obj):
        return obj.role.name if obj.role else None


class TempDocumentSerializer(serializers.ModelSerializer):
    """Serializer for temporary documents"""
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = TempDocument
        fields = [
            'id', 'user', 'user_name', 'client', 'application', 'document_name', 
            'document_type', 'status', 'uploaded_at', 'processed_at', 'metadata', 
            'document_path'
        ]
        read_only_fields = [
            'id', 'user', 'user_name', 'client', 'application', 'status', 
            'uploaded_at', 'processed_at'
        ]
    
    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}" if obj.user else None


class DocumentCategorySerializer(serializers.ModelSerializer):
    """Serializer for document categories"""
    document_types_count = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentCategory
        fields = [
            'id', 'category_seq', 'application', 'category_name', 'category_code',
            'description', 'order', 'document_types_count'
        ]
        read_only_fields = ['id', 'document_types_count']
    
    def get_document_types_count(self, obj):
        return obj.document_types.count()


class DocumentTypeSerializer(serializers.ModelSerializer):
    """Serializer for document types"""
    category_name = serializers.ReadOnlyField(source='category.category_name')
    
    class Meta:
        model = DocumentType
        fields = [
            'id', 'category', 'category_name', 'application', 'type_name', 
            'description', 'is_required', 'validation_rules', 'created_at', 
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'category_name']


class DocumentStageSerializer(serializers.ModelSerializer):
    """Serializer for document staging"""
    user_name = serializers.SerializerMethodField()
    category_name = serializers.ReadOnlyField(source='category.category_name')
    category_code = serializers.ReadOnlyField(source='category.category_code')
    approval_status = serializers.SerializerMethodField()
    approval_notes = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentStage
        fields = [
            'id', 'application', 'client', 'user', 'user_name', 'loan_application',
            'category', 'category_name', 'category_code', 'document_name', 
            'document_type', 'status', 'uploaded_at', 'processed_at', 
            'metadata', 'document_path', 'source', 'ai_confidence', 
            'ai_processing_details', 'approval_status', 'approval_notes'
        ]
        read_only_fields = [
            'id', 'user_name', 'category_name', 'category_code', 
            'approval_status', 'approval_notes'
        ]
    
    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}" if obj.user else None
    
    def get_approval_status(self, obj):
        if obj.metadata and 'approval_status' in obj.metadata:
            return obj.metadata['approval_status']
        return None
    
    def get_approval_notes(self, obj):
        if obj.metadata and 'approval_notes' in obj.metadata:
            return obj.metadata['approval_notes']
        return None


class DocumentProcessingLogSerializer(serializers.ModelSerializer):
    """Serializer for document processing logs"""
    
    class Meta:
        model = DocumentProcessingLog
        fields = ['id', 'document', 'status', 'message', 'timestamp']
        read_only_fields = ['id', 'timestamp']


class LoanApplicationSerializer(serializers.ModelSerializer):
    """Serializer for loan applications"""
    user_name = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    document_count = serializers.SerializerMethodField()
    
    class Meta:
        model = LoanApplication
        fields = [
            'id', 'application', 'client', 'user', 'user_name', 'loan_amount',
            'loan_purpose', 'loan_term', 'interest_rate', 'rate_expiry_date',
            'application_status', 'status_display', 'submission_date', 'decision_date',
            'credit_score', 'dti_ratio', 'case_readiness', 'document_index',
            'applicant_name', 'created_at', 'updated_at', 'document_count', 'metadata'
        ]
        read_only_fields = [
            'id', 'user_name', 'status_display', 'document_count', 
            'created_at', 'updated_at'
        ]
    
    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}" if obj.user else None
    
    def get_status_display(self, obj):
        return obj.get_application_status_display()
    
    def get_document_count(self, obj):
        return DocumentStage.objects.filter(loan_application=obj).count()