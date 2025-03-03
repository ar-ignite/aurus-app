# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
import json
from .models import Menu, CustomUser, Application, Client, TempDocument
from .serializers import TempDocumentSerializer
import os
import PyPDF2
import docx
from PIL import Image
import pytesseract
import requests
import json

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])  # Important to allow unauthenticated access
def login_view(request):
    try:
        # Get credentials from request
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {"error": "Username and password are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Authenticate user
        user = authenticate(username=username, password=password)
        
        if user is not None:
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            # Return user details and tokens
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'id': str(user.id),  # Convert UUID to string
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'role': user.role.name,
                    'client_id': str(user.client.id),  # Convert UUID to string
                    'application_id': str(user.application.id)  # Convert UUID to string
                }
            })
        else:
            return Response(
                {"error": "Invalid credentials"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
            
    except Exception as e:
        # Log the error for debugging
        print(f"Login error: {str(e)}")
        return Response(
            {"error": "Login failed due to server error"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def menu_list(request):
    user = request.user
    # Get all menus the user has access to through their groups
    user_groups = user.groups.all()
    menus = Menu.objects.filter(
        menupermission__group__in=user_groups
    ).distinct().select_related('parent').order_by('tree_id', 'lft')
    
    # Convert to hierarchical structure
    menu_dict = {}
    for menu in menus:
        menu_dict[menu.id] = {
            'id': menu.id,
            'name': menu.name,
            'path': menu.path,
            'parent_id': menu.parent_id,
            'children': []
        }
    
    # Build tree structure
    root_menus = []
    for menu_id, menu_data in menu_dict.items():
        if menu_data['parent_id'] is None:
            root_menus.append(menu_data)
        else:
            parent = menu_dict.get(menu_data['parent_id'])
            if parent:
                parent['children'].append(menu_data)
    
    return Response(root_menus)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def document_upload(request):
    user = request.user
    
    # Create temporary document record
    # In a real implementation, you would handle the file upload
    data = {
        'document_name': request.data.get('document_name'),
        'document_type': request.data.get('document_type'),
        'status': 'pending',
        'user_id': str(user.id),
        'client_id': str(user.client.id),
        'application_id': str(user.application.id),
        'metadata': request.data.get('metadata', {})
    }
    
    # In a real implementation, save this to your temp table
    
    return Response(data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def document_list(request):
    # Mock data for demonstration
    documents = [
        {
            'id': '1',
            'document_name': 'Mortgage_Application.pdf',
            'document_type': 'Application',
            'status': 'processed',
            'uploaded_at': '2024-02-24T15:30:00Z',
            'processed_at': '2024-02-24T15:35:00Z',
            'metadata': {'pages': 5, 'size': '1.2MB'}
        },
        {
            'id': '2',
            'document_name': 'Income_Verification.pdf',
            'document_type': 'Verification',
            'status': 'pending',
            'uploaded_at': '2024-02-24T16:00:00Z',
            'processed_at': None,
            'metadata': {'pages': 2, 'size': '0.8MB'}
        }
    ]
    return Response(documents)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def application_list(request):
    applications = Application.objects.all()
    data = [{'id': str(app.id), 'name': app.name} for app in applications]
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def client_list(request):
    clients = Client.objects.all()
    data = [{'id': str(client.id), 'name': client.name} for client in clients]
    return Response(data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def document_upload(request):
    user = request.user
    
    # Handle file upload
    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Create temporary document record
    document_data = {
        'user': user,
        'client': user.client,
        'application': user.application,
        'document_name': uploaded_file.name,
        'document_type': request.data.get('document_type', 'Other'),
        'status': 'pending',
        'metadata': {
            'size': uploaded_file.size,
            'content_type': uploaded_file.content_type
        }
    }
    
    # In production, save the file to storage (e.g., S3, filesystem)
    # file_path = save_file_to_storage(uploaded_file)
    # document_data['document_path'] = file_path
    
    temp_document = TempDocument.objects.create(**document_data)
    
    serializer = TempDocumentSerializer(temp_document)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


from django.utils import timezone
from .utils.storage import DocumentStorage
from .models import TempDocument
from .serializers import TempDocumentSerializer

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def document_upload(request):
    """Handle document upload and create a temporary document record"""
    user = request.user
    
    # Validate input
    if 'file' not in request.FILES:
        return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    uploaded_file = request.FILES['file']
    document_type = request.data.get('document_type', 'Other')
    
    # Basic validation - can be expanded based on requirements
    if uploaded_file.size > 10 * 1024 * 1024:  # 10MB limit
        return Response({'error': 'File too large. Maximum size is 10MB'}, 
                        status=status.HTTP_400_BAD_REQUEST)
    
    # Accept only certain file types
    allowed_types = ['application/pdf', 'image/jpeg', 'image/png', 
                     'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
    if uploaded_file.content_type not in allowed_types:
        return Response({'error': 'File type not supported'}, 
                        status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Save file to storage
        file_path = DocumentStorage.save_document(uploaded_file, document_type)
        
        # Create temporary document record
        temp_document = TempDocument.objects.create(
            user=user,
            client=user.client,
            application=user.application,
            document_name=uploaded_file.name,
            document_type=document_type,
            status='pending',
            document_path=file_path,
            metadata={
                'size': uploaded_file.size,
                'content_type': uploaded_file.content_type
            }
        )
        
        serializer = TempDocumentSerializer(temp_document)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        # Log the error
        print(f"Error in document upload: {e}")
        return Response({'error': 'Failed to process document upload'}, 
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def document_list(request):
    """List all documents for the current user"""
    user = request.user
    
    # Filter by user, and optionally by status
    status_filter = request.query_params.get('status')
    if status_filter:
        documents = TempDocument.objects.filter(user=user, status=status_filter)
    else:
        documents = TempDocument.objects.filter(user=user)
    
    serializer = TempDocumentSerializer(documents, many=True)
    return Response(serializer.data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def document_process(request, document_id):
    """Mark a document as processed"""
    try:
        document = TempDocument.objects.get(id=document_id)
        
        # Security check - only allow access to own documents
        if document.user != request.user:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        
        document.status = 'processed'
        document.processed_at = timezone.now()
        document.save()
        
        serializer = TempDocumentSerializer(document)
        return Response(serializer.data)
    
    except TempDocument.DoesNotExist:
        return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def document_delete(request, document_id):
    """Delete a document"""
    try:
        document = TempDocument.objects.get(id=document_id)
        
        # Security check - only allow access to own documents
        if document.user != request.user:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        
        # Delete the file from storage
        if document.document_path:
            DocumentStorage.delete_document(document.document_path)
        
        # Delete the database record
        document.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    except TempDocument.DoesNotExist:
        return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)

def health_check(request):
    return JsonResponse({"status": "ok"})


from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Menu, MenuRole, Role, CustomUser
from .serializers import MenuSerializer, RoleSerializer

class IsAuthenticatedAndActive(permissions.BasePermission):
    """
    Custom permission to only allow active authenticated users
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_active

@api_view(['GET'])
@permission_classes([IsAuthenticatedAndActive])
def user_menu_tree(request):
    """Get the menu tree structure for the current user based on their role"""
    user = request.user
    
    if not user.role:
        return Response({"error": "User does not have an assigned role"}, status=status.HTTP_403_FORBIDDEN)
    
    # Get all accessible menus for this user's role
    accessible_menu_ids = MenuRole.objects.filter(
        role=user.role, 
        can_view=True
    ).values_list('menu_id', flat=True)
    
    # Get root level menus first
    root_menus = Menu.objects.filter(
        id__in=accessible_menu_ids,
        parent__isnull=True
    ).order_by('order')
    
    # Build the tree recursively
    def build_menu_tree(menus):
        result = []
        for menu in menus:
            # Check if this menu has accessible children
            children = Menu.objects.filter(
                id__in=accessible_menu_ids,
                parent=menu
            ).order_by('order')
            
            menu_data = {
                'id': str(menu.id),
                'name': menu.name,
                'path': menu.path,
                'children': build_menu_tree(children) if children.exists() else []
            }
            result.append(menu_data)
        return result
    
    menu_tree = build_menu_tree(root_menus)
    
    return Response(menu_tree)

@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def all_roles(request):
    """Get all available roles (admin only)"""
    roles = Role.objects.all()
    serializer = RoleSerializer(roles, many=True)
    return Response(serializer.data)


# views.py - Document Processing APIs
import json
import os
import uuid
from datetime import datetime
from django.http import JsonResponse
from django.conf import settings
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Count, Q

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

import requests
from .models import (
    CustomUser, Application, Client, DocumentCategory, DocumentType,
    TempDocument, DocumentStage, DocumentProcessingLog, LoanApplication
)
from .serializers import (
    TempDocumentSerializer, DocumentStageSerializer, DocumentCategorySerializer,
    DocumentTypeSerializer, LoanApplicationSerializer
)
from .utils.storage import DocumentStorage

import openai
# Together AI API configuration
TOGETHER_API_KEY = os.environ.get('TOGETHER_API_KEY', '3af172c290b1170851ca622ca774248e341da8f6e43a24e5311f8da41191d4dc')

client = openai.OpenAI(
    base_url = "https://api.together.xyz/v1",
    api_key = '3af172c290b1170851ca622ca774248e341da8f6e43a24e5311f8da41191d4dc',
)

# Document categories mapping
DOCUMENT_CATEGORIES = {
    "identification": "Identification Documents",
    "income": "Income Verification",
    "asset": "Asset Documentation",
    "credit": "Credit History",
    "property": "Property Information",
    "debt": "Debt Obligations",
    "down_payment": "Down Payment Verification",
    "loan_specific": "Loan-Specific Requirements",
    "additional": "Additional Documentation",
    "untagged": "Untagged"
}

# ===============================================
# Document Upload and AI Processing APIs
# ===============================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def document_upload(request):
    """
    Handle document upload to temp storage before AI processing
    """
    user = request.user
    loan_application_id = request.data.get('loan_application_id')
    
    # Validate loan application exists and belongs to user
    try:
        if loan_application_id:
            loan_application = LoanApplication.objects.get(
                id=loan_application_id, 
                user=user
            )
        else:
            return Response(
                {'error': 'Loan application ID is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    except LoanApplication.DoesNotExist:
        return Response(
            {'error': 'Loan application not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Validate input
    if 'file' not in request.FILES:
        return Response(
            {'error': 'No file provided'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    uploaded_file = request.FILES['file']
    document_type = request.data.get('document_type', 'Unknown')
    
    # Basic validation - can be expanded based on requirements
    if uploaded_file.size > 20 * 1024 * 1024:  # 20MB limit
        return Response(
            {'error': 'File too large. Maximum size is 20MB'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Accept only certain file types
    allowed_types = ['application/pdf', 'image/jpeg', 'image/png', 
                     'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
    
    if uploaded_file.content_type not in allowed_types:
        return Response(
            {'error': 'File type not supported. Supported types are PDF, JPEG, PNG, and Word documents'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Save file to storage
        file_path = DocumentStorage.save_document(uploaded_file, document_type)
        
        # Create temporary document record
        temp_document = TempDocument.objects.create(
            user=user,
            client=user.client,
            application=user.application,
            document_name=uploaded_file.name,
            document_type=document_type,
            status='pending',
            document_path=file_path,
            metadata={
                'size': uploaded_file.size,
                'content_type': uploaded_file.content_type,
                'loan_application_id': str(loan_application_id),
                'upload_timestamp': timezone.now().isoformat()
            }
        )
        
        # Start AI processing in background
        # In a production environment, this would be done with a task queue (Celery)
        # For simplicity, we call it directly here
        process_document_with_ai(temp_document.id)
        
        serializer = TempDocumentSerializer(temp_document)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        # Log the error
        print(f"Error in document upload: {e}")
        return Response(
            {'error': f'Failed to process document upload: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def process_document_with_ai(request, document_id=None):
    """
    Process a document with Together AI to categorize it
    Can be called directly or via endpoint
    """
    user = request.user if request else None
    
    # If called as an API endpoint with a request
    if request and not isinstance(request, int):
        try:
            temp_document = TempDocument.objects.get(id=document_id)
            # Security check
            if temp_document.user != user:
                return Response(
                    {'error': 'You do not have permission to process this document'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        except TempDocument.DoesNotExist:
            return Response(
                {'error': 'Document not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    else:
        # If called directly with document_id
        try:
            document_id = request if request else document_id
            temp_document = TempDocument.objects.get(id=document_id)
            user = temp_document.user
        except TempDocument.DoesNotExist:
            print(f"Document not found: {document_id}")
            return None if not request else Response(
                {'error': 'Document not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    # Update status to processing
    temp_document.status = 'processing'
    temp_document.save()
    
    try:
        # In a real implementation, you would extract text from the document
        # For simplicity, we'll simulate this with the file name and type
        document_text = f"Document name: {temp_document.document_name}, Type: {temp_document.document_type}"
        
        # In production, you would read the file and extract text
        # file_content = DocumentStorage.read_document(temp_document.document_path)
        # document_text = extract_text_from_document(file_content)
        
        # Prepare prompt for Together AI categorization
        prompt = f"""
        Your task is to categorize this document into one of the following categories:
        - identification: Government-issued ID, SSN, etc.
        - income: Pay stubs, W-2s, tax returns, etc.
        - asset: Bank statements, investment accounts, etc.
        - credit: Credit reports, credit score, etc.
        - property: Property details, appraisal, etc.
        - debt: Existing loans, credit card debt, etc.
        - down_payment: Proof of down payment funds
        - loan_specific: Specific documents for the loan
        - additional: Other supporting documents
        - untagged: Documents not yet categorized
        
        Document to categorize:
        {document_text}
        
        Return only the category code (e.g., "identification") and nothing else.
        """
        
        # Call Together AI API
        ai_category = call_together_ai(prompt, user)
        
        # If AI couldn't categorize, mark as untagged
        if not ai_category:
            ai_category = "untagged"
            ai_confidence = 0.0
        else:
            # Strip whitespace and validate category
            ai_category = ai_category.strip().lower()
            if ai_category not in DOCUMENT_CATEGORIES:
                ai_category = "untagged"
                ai_confidence = 0.0
            else:
                ai_confidence = 0.85  # Mock confidence for this example
        
        # Get the corresponding category from our database
        try:
            category = DocumentCategory.objects.get(
                application=temp_document.application,
                category_code=ai_category
            )
        except DocumentCategory.DoesNotExist:
            # If category doesn't exist, use untagged
            category = DocumentCategory.objects.get(
                application=temp_document.application,
                category_code="untagged"
            )
        
        # Get loan application ID from metadata
        loan_application_id = temp_document.metadata.get('loan_application_id')
        loan_application = None
        if loan_application_id:
            try:
                loan_application = LoanApplication.objects.get(id=loan_application_id)
            except LoanApplication.DoesNotExist:
                pass
                
        if not loan_application:
            # Get the user's most recent loan application if not specified
            loan_application = LoanApplication.objects.filter(
                user=user
            ).order_by('-created_at').first()
            
            if not loan_application:
                # Create a draft loan application if none exists
                loan_application = LoanApplication.objects.create(
                    application=user.application,
                    client=user.client,
                    user=user,
                    loan_amount=0,
                    loan_purpose="Document Upload",
                    loan_term=30,
                    application_status="DRAFT",
                    applicant_name=f"{user.first_name} {user.last_name}"
                )
        
        # Create a document in the document_stage table
        with transaction.atomic():
            document_stage = DocumentStage.objects.create(
                application=temp_document.application,
                client=temp_document.client,
                user=user,
                loan_application=loan_application,
                category=category,
                document_name=temp_document.document_name,
                document_type=temp_document.document_type,
                status='COMPLETED',
                document_path=temp_document.document_path,
                source='MANUAL',
                ai_confidence=ai_confidence,
                ai_processing_details={
                    'categorization': ai_category,
                    'confidence': ai_confidence,
                    'processing_time': timezone.now().isoformat()
                },
                metadata=temp_document.metadata
            )
            
            # Create a processing log entry
            DocumentProcessingLog.objects.create(
                document=document_stage,
                status='COMPLETED',
                message=f"Document processed successfully and categorized as {category.category_name}"
            )
            
            # Update temp document status
            temp_document.status = 'processed'
            temp_document.processed_at = timezone.now()
            temp_document.save()
            
            # Update loan application metrics
            update_loan_application_metrics(loan_application)
        
        result = {
            'status': 'success',
            'document_id': str(document_stage.id),
            'category': category.category_name,
            'category_code': category.category_code,
            'confidence': ai_confidence
        }
        
        return None if not isinstance(request, (list, dict)) else Response(result, status=status.HTTP_200_OK)
    
    except Exception as e:
        # Log the error
        print(f"Error processing document with AI: {e}")
        
        # Update status to failed
        temp_document.status = 'failed'
        temp_document.save()
        
        if isinstance(request, (list, dict)) or not request:
            return None
        
        return Response(
            {'error': f'Failed to process document: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def document_upload(request):
    """
    Handle document upload to temp storage before AI processing
    """
    user = request.user
    loan_application_id = request.data.get('loan_application_id')
    
    # Validate loan application exists and belongs to user
    try:
        if loan_application_id:
            loan_application = LoanApplication.objects.get(
                id=loan_application_id
            )
        else:
            return Response(
                {'error': 'Loan application ID is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    except LoanApplication.DoesNotExist:
        return Response(
            {'error': 'Loan application not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Validate input
    if 'file' not in request.FILES:
        return Response(
            {'error': 'No file provided'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    uploaded_file = request.FILES['file']
    document_type = request.data.get('document_type', 'Unknown')
    
    # Basic validation - can be expanded based on requirements
    if uploaded_file.size > 20 * 1024 * 1024:  # 20MB limit
        return Response(
            {'error': 'File too large. Maximum size is 20MB'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Accept only certain file types
    allowed_types = ['application/pdf', 'image/jpeg', 'image/png', 
                     'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
    
    if uploaded_file.content_type not in allowed_types:
        return Response(
            {'error': 'File type not supported. Supported types are PDF, JPEG, PNG, and Word documents'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Save file to storage
        file_path = DocumentStorage.save_document(uploaded_file, document_type)
        
        # Create temporary document record
        temp_document = TempDocument.objects.create(
            user=user,
            client=user.client,
            application=user.application,
            document_name=uploaded_file.name,
            document_type=document_type,
            status='pending',
            document_path=file_path,
            metadata={
                'size': uploaded_file.size,
                'content_type': uploaded_file.content_type,
                'loan_application_id': str(loan_application_id),
                'upload_timestamp': timezone.now().isoformat()
            }
        )
        
        # Process document with AI (but don't wait for processing to complete)
        # DON'T pass the request object to the processing function
        # Instead, schedule the processing with the document ID
        try:
            # This would be better handled with a task queue like Celery in production
            process_document_with_ai_task(temp_document.id)
        except Exception as e:
            # If AI processing fails, we still want to return success for the upload
            print(f"Error starting AI processing: {e}")
        
        serializer = TempDocumentSerializer(temp_document)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        # Log the error
        print(f"Error in document upload: {e}")
        return Response(
            {'error': f'Failed to process document upload: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Separate function to process document with AI that doesn't expect a request object
def process_document_with_ai_task(document_id):
    """
    Process a document with Together AI to categorize it
    This function is meant to be called as a background task, not directly from an API view
    """
    try:
        temp_document = TempDocument.objects.get(id=document_id)
        user = temp_document.user
        
        # Update status to processing
        temp_document.status = 'processing'
        temp_document.save()
        
        # In a real implementation, you would extract text from the document
        # For simplicity, we'll simulate this with the file name and type
        document_text = f"Document name: {temp_document.document_name}, Type: {temp_document.document_type}"
        
        # In production, you would read the file and extract text
        # file_content = DocumentStorage.read_document(temp_document.document_path)
        # document_text = extract_text_from_document(file_content)
        
        # Prepare prompt for Together AI categorization
        prompt = f"""
        Your task is to categorize this document into one of the following categories:
        - identification: Government-issued ID, SSN, etc.
        - income: Pay stubs, W-2s, tax returns, etc.
        - asset: Bank statements, investment accounts, etc.
        - credit: Credit reports, credit score, etc.
        - property: Property details, appraisal, etc.
        - debt: Existing loans, credit card debt, etc.
        - down_payment: Proof of down payment funds
        - loan_specific: Specific documents for the loan
        - additional: Other supporting documents
        - untagged: Documents not yet categorized
        
        Document to categorize:
        {document_text}
        
        Return only the category code (e.g., "identification") and nothing else.
        """
        
        # Call Together AI API (or simulate it)
        ai_category = call_together_ai(prompt, user)
        
        # Simulate AI categorization based on the document name
        # If AI couldn't categorize, mark as untagged
        if not ai_category:
            ai_category = "untagged"
            ai_confidence = 0.0
        else:
            # Strip whitespace and validate category
            ai_category = ai_category.strip().lower()
            if ai_category not in DOCUMENT_CATEGORIES:
                ai_category = "untagged"
                ai_confidence = 0.0
            else:
                ai_confidence = 0.85  # Mock confidence for this example
        
        # Get the corresponding category from our database
        try:
            category = DocumentCategory.objects.get(
                application=temp_document.application,
                category_code=ai_category
            )
        except DocumentCategory.DoesNotExist:
            # If category doesn't exist, use untagged
            category = DocumentCategory.objects.get(
                application=temp_document.application,
                category_code="untagged"
            )
        
        # Get loan application ID from metadata
        loan_application_id = temp_document.metadata.get('loan_application_id')
        
        try:
            loan_application = LoanApplication.objects.get(id=loan_application_id)
        except LoanApplication.DoesNotExist:
            # Fallback to user's most recent loan if the specific one isn't found
            loan_application = LoanApplication.objects.filter(
                user=user
            ).order_by('-created_at').first()
            
        if not loan_application:
            # We need a loan application, so create a draft if none exists
            loan_application = LoanApplication.objects.create(
                application=user.application,
                client=user.client,
                user=user,
                loan_amount=0,
                loan_purpose="Document Upload",
                loan_term=30,
                application_status="DRAFT",
                applicant_name=f"{user.first_name} {user.last_name}"
            )
        
        # Create a document in the document_stage table
        with transaction.atomic():
            document_stage = DocumentStage.objects.create(
                application=temp_document.application,
                client=temp_document.client,
                user=user,
                loan_application=loan_application,
                category=category,
                document_name=temp_document.document_name,
                document_type=temp_document.document_type,
                status='COMPLETED',
                document_path=temp_document.document_path,
                source='MANUAL',
                ai_confidence=ai_confidence,
                ai_processing_details={
                    'categorization': ai_category,
                    'confidence': ai_confidence,
                    'processing_time': timezone.now().isoformat()
                },
                metadata=temp_document.metadata
            )
            
            # Create a processing log entry
            DocumentProcessingLog.objects.create(
                document=document_stage,
                status='COMPLETED',
                message=f"Document processed successfully and categorized as {category.category_name}"
            )
            
            # Update temp document status
            temp_document.status = 'processed'
            temp_document.processed_at = timezone.now()
            temp_document.save()
            
            # Update loan application metrics (case readiness, document index)
            update_loan_application_metrics(loan_application)
        
        return True
    
    except Exception as e:
        # Log the error
        print(f"Error processing document with AI: {e}")
        
        try:
            # Update status to failed if we have a document
            temp_document = TempDocument.objects.get(id=document_id)
            temp_document.status = 'failed'
            temp_document.save()
        except:
            pass
            
        return False


def call_together_ai(prompt, user):
    """
    Call Together AI API to process the document text and categorize it
    """
    try:
        # In a real implementation, you would call the Together AI API
        # For this example, we'll simulate a response
        
        # Uncomment to use actual Together AI API

        response = client.chat.completions.create(
            model="meta-llama/Meta-Llama-3-8B-Instruct-Turbo",
            messages=[{"role": "user", "content": prompt}],
        )
        
        print(response.choices[0].message.content)
        
        ai_response = response.choices[0].message.content
        return ai_response
        # Simulate AI categorization based on document name
        document_keywords = {
            "id": "identification",
            "license": "identification",
            "passport": "identification",
            "ssn": "identification",
            "paystub": "income",
            "pay stub": "income",
            "w-2": "income",
            "tax return": "income",
            "bank": "asset",
            "statement": "asset",
            "credit": "credit",
            "report": "credit",
            "score": "credit",
            "property": "property",
            "appraisal": "property",
            "loan": "debt",
            "debt": "debt",
            "down payment": "down_payment",
            "mortgage": "loan_specific",
        }
        
        # Extract the document name from the prompt
        doc_name_start = prompt.find("Document name:")
        doc_name_end = prompt.find(",", doc_name_start)
        if doc_name_start > 0 and doc_name_end > 0:
            doc_name = prompt[doc_name_start + 14:doc_name_end].lower().strip()
            
            # Check for keywords
            for keyword, category in document_keywords.items():
                if keyword in doc_name:
                    return category
        
        # Default to untagged if no match found
        return "untagged"
        
    except Exception as e:
        print(f"Error calling Together AI: {e}")
        return None


def update_loan_application_metrics(loan_application):
    """
    Update loan application metrics based on document status
    """
    if not loan_application:
        return
    
    # Count total documents and completed documents
    total_docs = DocumentStage.objects.filter(
        loan_application=loan_application
    ).count()
    
    completed_docs = DocumentStage.objects.filter(
        loan_application=loan_application,
        status='COMPLETED'
    ).count()
    
    # Get document categories for this application
    required_categories = DocumentCategory.objects.filter(
        application=loan_application.application
    ).values_list('id', flat=True)
    
    # Count how many required categories have at least one document
    categories_with_docs = DocumentStage.objects.filter(
        loan_application=loan_application,
        category_id__in=required_categories
    ).values('category_id').distinct().count()
    
    # Calculate case readiness (% of required categories with documents)
    if required_categories.count() > 0:
        case_readiness = int((categories_with_docs / required_categories.count()) * 100)
    else:
        case_readiness = 0
    
    # Calculate document index (% of documents that are processed)
    document_index = int((completed_docs / max(total_docs, 1)) * 100)
    
    # Update loan application
    loan_application.case_readiness = case_readiness
    loan_application.document_index = document_index
    loan_application.save()
    
    return


# ===============================================
# Document Category and Type APIs
# ===============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def document_categories(request):
    """
    Get all document categories
    """
    user = request.user
    categories = DocumentCategory.objects.filter(
        application=user.application
    ).order_by('order')
    
    serializer = DocumentCategorySerializer(categories, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def document_types(request, category_id=None):
    """
    Get all document types for a specific category or all types
    """
    user = request.user
    
    if category_id:
        types = DocumentType.objects.filter(
            application=user.application,
            category_id=category_id
        ).order_by('type_name')
    else:
        types = DocumentType.objects.filter(
            application=user.application
        ).order_by('category__order', 'type_name')
    
    serializer = DocumentTypeSerializer(types, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_document_category(request):
    """
    Create a new document category
    """
    user = request.user
    
    # Check if user has permission
    if not user.role or not user.role.name in ['CEO', 'CTO', 'Admin']:
        return Response(
            {'error': 'You do not have permission to create document categories'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    data = request.data.copy()
    data['application'] = user.application.id
    
    # Get next available order number
    next_order = DocumentCategory.objects.filter(
        application=user.application
    ).count() + 1
    
    # Generate a sequence number (increments of 10)
    data['category_seq'] = str(next_order * 10)
    data['order'] = next_order
    
    serializer = DocumentCategorySerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_document_type(request):
    """
    Create a new document type
    """
    user = request.user
    
    # Check if user has permission
    if not user.role or not user.role.name in ['CEO', 'CTO', 'Admin']:
        return Response(
            {'error': 'You do not have permission to create document types'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    data = request.data.copy()
    data['application'] = user.application.id
    
    serializer = DocumentTypeSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ===============================================
# Document Listing and Management APIs
# ===============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def document_list(request, loan_application_id=None):
    """
    List all documents for a loan application or all user documents
    """
    user = request.user
    
    if loan_application_id:
        # Check if loan application belongs to user
        try:
            loan_application = LoanApplication.objects.get(id=loan_application_id)
            
            # Allow loan officers to view any application
            if user.role and user.role.name != 'Loan Officer' and loan_application.user != user:
                return Response(
                    {'error': 'You do not have permission to view this loan application'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
                
            documents = DocumentStage.objects.filter(
                loan_application_id=loan_application_id
            ).order_by('-uploaded_at')
        except LoanApplication.DoesNotExist:
            return Response(
                {'error': 'Loan application not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    else:
        # Get all documents for the user's loans
        if user.role and user.role.name == 'Loan Officer':
            # Loan officers see all documents
            documents = DocumentStage.objects.filter(
                application=user.application
            ).order_by('-uploaded_at')
        else:
            # Regular users only see their documents
            documents = DocumentStage.objects.filter(
                user=user
            ).order_by('-uploaded_at')
    
    serializer = DocumentStageSerializer(documents, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def document_details(request, document_id):
    """
    Get details for a specific document
    """
    user = request.user
    
    try:
        document = DocumentStage.objects.get(id=document_id)
        
        # Check if user has permission to view this document
        if user.role and user.role.name == 'Loan Officer':
            # Loan officers can view any document
            pass
        elif document.user != user:
            return Response(
                {'error': 'You do not have permission to view this document'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = DocumentStageSerializer(document)
        return Response(serializer.data)
    except DocumentStage.DoesNotExist:
        return Response(
            {'error': 'Document not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_document_category(request, document_id):
    """
    Update a document's category (manual override of AI categorization)
    """
    user = request.user
    
    try:
        document = DocumentStage.objects.get(id=document_id)
        
        # Check if user has permission to update this document
        if not user.role or (user.role.name not in ['CEO', 'CTO', 'Admin', 'Loan Officer'] and document.user != user):
            return Response(
                {'error': 'You do not have permission to update this document'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update category
        category_id = request.data.get('category_id')
        if not category_id:
            return Response(
                {'error': 'Category ID is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            category = DocumentCategory.objects.get(id=category_id)
            
            # Update document category
            document.category = category
            document.ai_processing_details = {
                **(document.ai_processing_details or {}),
                'manual_override': {
                    'previous_category': document.category.category_code if document.category else None,
                    'override_by': str(user.id),
                    'override_time': timezone.now().isoformat()
                }
            }
            document.save()
            
            # Log the change
            DocumentProcessingLog.objects.create(
                document=document,
                status='COMPLETED',
                message=f"Document category manually updated to {category.category_name} by {user.username}"
            )
            
            # Update loan application metrics
            update_loan_application_metrics(document.loan_application)
            
            serializer = DocumentStageSerializer(document)
            return Response(serializer.data)
        except DocumentCategory.DoesNotExist:
            return Response(
                {'error': 'Category not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
    except DocumentStage.DoesNotExist:
        return Response(
            {'error': 'Document not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def approve_reject_document(request, document_id):
    """
    Approve or reject a document (loan officer only)
    """
    user = request.user
    
    # Check if user has permission
    if not user.role or user.role.name not in ['CEO', 'CTO', 'Admin', 'Loan Officer']:
        return Response(
            {'error': 'You do not have permission to approve or reject documents'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        document = DocumentStage.objects.get(id=document_id)
        action = request.data.get('action', '').upper()
        notes = request.data.get('notes', '')
        
        if action not in ['APPROVE', 'REJECT']:
            return Response(
                {'error': 'Invalid action. Must be APPROVE or REJECT'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update document
        document.metadata = {
            **(document.metadata or {}),
            'approval_status': 'APPROVED' if action == 'APPROVE' else 'REJECTED',
            'approval_by': str(user.id),
            'approval_time': timezone.now().isoformat(),
            'approval_notes': notes
        }
        document.save()
        
        # Log the action
        DocumentProcessingLog.objects.create(
            document=document,
            status='COMPLETED',
            message=f"Document {action.lower()}ed by {user.username}: {notes}"
        )
        
        serializer = DocumentStageSerializer(document)
        return Response(serializer.data)
    except DocumentStage.DoesNotExist:
        return Response(
            {'error': 'Document not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_document(request, document_id):
    """
    Delete a document
    """
    user = request.user
    
    try:
        document = DocumentStage.objects.get(id=document_id)
        
        # Check if user has permission to delete this document
        if not user.role or (user.role.name not in ['CEO', 'CTO', 'Admin'] and document.user != user):
            return Response(
                {'error': 'You do not have permission to delete this document'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if document is approved
        approval_status = document.metadata.get('approval_status', '') if document.metadata else ''
        if approval_status == 'APPROVED' and (not user.role or user.role.name not in ['CEO', 'CTO', 'Admin']):
            return Response(
                {'error': 'Approved documents can only be deleted by an administrator'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Delete the physical file
        if document.document_path:
            DocumentStorage.delete_document(document.document_path)
        
        # Store the loan application for updating metrics after deletion
        loan_application = document.loan_application
        
        # Delete document
        document.delete()
        
        # Update loan application metrics
        update_loan_application_metrics(loan_application)
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    except DocumentStage.DoesNotExist:
        return Response(
            {'error': 'Document not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )


# ===============================================
# Loan Application APIs
# ===============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def loan_applications(request):
    """
    Get all loan applications for the current user
    """
    user = request.user
    
    # Determine which loan applications to return based on user role
    if user.role and user.role.name in ['CEO', 'CTO', 'Admin', 'Loan Officer']:
        # Admins and loan officers see all applications
        applications = LoanApplication.objects.filter(
            application=user.application
        ).order_by('-created_at')
    else:
        # Regular users only see their applications
        applications = LoanApplication.objects.filter(
            user=user
        ).order_by('-created_at')
    
    serializer = LoanApplicationSerializer(applications, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def loan_application_details(request, loan_id):
    """
    Get details for a specific loan application
    """
    user = request.user
    
    try:
        loan_application = LoanApplication.objects.get(id=loan_id)
        
        # Check if user has permission to view this loan
        if user.role and user.role.name in ['CEO', 'CTO', 'Admin', 'Loan Officer']:
            # Admin users can view any loan
            pass
        elif loan_application.user != user:
            return Response(
                {'error': 'You do not have permission to view this loan application'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = LoanApplicationSerializer(loan_application)
        return Response(serializer.data)
    except LoanApplication.DoesNotExist:
        return Response(
            {'error': 'Loan application not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_loan_application(request):
    """
    Create a new loan application
    """
    user = request.user
    
    data = request.data.copy()
    data['user'] = user.id
    data['client'] = user.client.id
    data['application'] = user.application.id
    data['application_status'] = 'DRAFT'
    
    # Set default applicant name if not provided
    if not data.get('applicant_name'):
        data['applicant_name'] = f"{user.first_name} {user.last_name}"
    
    serializer = LoanApplicationSerializer(data=data)
    if serializer.is_valid():
        loan_application = serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_loan_application(request, loan_id):
    """
    Update a loan application
    """
    user = request.user
    
    try:
        loan_application = LoanApplication.objects.get(id=loan_id)
        
        # Check if user has permission to update this loan
        if user.role and user.role.name in ['CEO', 'CTO', 'Admin', 'Loan Officer']:
            # Admin users can update any loan
            pass
        elif loan_application.user != user:
            return Response(
                {'error': 'You do not have permission to update this loan application'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Only allow updates to DRAFT or SUBMITTED loans
        if loan_application.application_status not in ['DRAFT', 'SUBMITTED'] and not user.role:
            return Response(
                {'error': f'Cannot update loan in {loan_application.application_status} status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = request.data.copy()
        
        # Don't allow changing user, client, or application
        if 'user' in data:
            del data['user']
        if 'client' in data:
            del data['client']
        if 'application' in data:
            del data['application']
        
        serializer = LoanApplicationSerializer(loan_application, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except LoanApplication.DoesNotExist:
        return Response(
            {'error': 'Loan application not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_loan_application(request, loan_id):
    """
    Submit a loan application for review
    """
    user = request.user
    
    try:
        loan_application = LoanApplication.objects.get(id=loan_id)
        
        # Check if user has permission to submit this loan
        if loan_application.user != user:
            return Response(
                {'error': 'You do not have permission to submit this loan application'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Only allow submission of DRAFT loans
        if loan_application.application_status != 'DRAFT':
            return Response(
                {'error': f'Cannot submit loan in {loan_application.application_status} status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update status and submission date
        loan_application.application_status = 'SUBMITTED'
        loan_application.submission_date = timezone.now()
        loan_application.save()
        
        serializer = LoanApplicationSerializer(loan_application)
        return Response(serializer.data)
    except LoanApplication.DoesNotExist:
        return Response(
            {'error': 'Loan application not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_loan_application(request, loan_id):
    """
    Process a loan application (change status to UNDER_REVIEW, APPROVED, or REJECTED)
    """
    user = request.user
    
    # Check if user has permission
    if not user.role or user.role.name not in ['CEO', 'CTO', 'Admin', 'Loan Officer']:
        return Response(
            {'error': 'You do not have permission to process loan applications'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        loan_application = LoanApplication.objects.get(id=loan_id)
        
        # Get action and notes
        action = request.data.get('action', '').upper()
        notes = request.data.get('notes', '')
        
        # Validate action
        valid_actions = ['REVIEW', 'APPROVE', 'REJECT', 'UNDERWRITER']
        if action not in valid_actions:
            return Response(
                {'error': f'Invalid action. Must be one of: {", ".join(valid_actions)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate current status for the action
        if action == 'REVIEW' and loan_application.application_status != 'SUBMITTED':
            return Response(
                {'error': 'Can only move to UNDER_REVIEW from SUBMITTED status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        elif action in ['APPROVE', 'REJECT'] and loan_application.application_status not in ['UNDER_REVIEW', 'UNDERWRITER']:
            return Response(
                {'error': f'Can only {action} from UNDER_REVIEW or UNDERWRITER status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        elif action == 'UNDERWRITER' and loan_application.application_status != 'UNDER_REVIEW':
            return Response(
                {'error': 'Can only move to UNDERWRITER from UNDER_REVIEW status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update loan application status
        if action == 'REVIEW':
            loan_application.application_status = 'UNDER_REVIEW'
        elif action == 'APPROVE':
            loan_application.application_status = 'APPROVED'
            loan_application.decision_date = timezone.now()
        elif action == 'REJECT':
            loan_application.application_status = 'REJECTED'
            loan_application.decision_date = timezone.now()
        elif action == 'UNDERWRITER':
            loan_application.application_status = 'UNDERWRITER'
        
        # Add processing notes to metadata
        loan_application.metadata = {
            **(loan_application.metadata or {}),
            'processing_history': [
                *((loan_application.metadata or {}).get('processing_history', [])),
                {
                    'action': action,
                    'previous_status': loan_application.application_status,
                    'new_status': loan_application.get_application_status_display(),
                    'processed_by': str(user.id),
                    'processor_name': f"{user.first_name} {user.last_name}",
                    'processed_at': timezone.now().isoformat(),
                    'notes': notes
                }
            ]
        }
        
        loan_application.save()
        
        serializer = LoanApplicationSerializer(loan_application)
        return Response(serializer.data)
    except LoanApplication.DoesNotExist:
        return Response(
            {'error': 'Loan application not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )


# ===============================================
# AI Letter Generation API
# ===============================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_ai_letter(request, loan_id):
    """
    Generate an AI letter based on loan application status and documents
    """
    user = request.user
    
    try:
        loan_application = LoanApplication.objects.get(id=loan_id)
        
        # Check if user has permission to view this loan
        if user.role and user.role.name in ['CEO', 'CTO', 'Admin', 'Loan Officer']:
            # Admin users can generate letters for any loan
            pass
        elif loan_application.user != user:
            return Response(
                {'error': 'You do not have permission to generate letters for this loan application'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get letter type
        letter_type = request.data.get('letter_type', '').upper()
        
        valid_types = ['WELCOME', 'STATUS_UPDATE', 'DOCUMENT_REQUEST', 'APPROVAL', 'REJECTION']
        if letter_type not in valid_types:
            return Response(
                {'error': f'Invalid letter type. Must be one of: {", ".join(valid_types)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # For document request letters, get the list of missing documents
        missing_documents = []
        if letter_type == 'DOCUMENT_REQUEST':
            # Find required document types that don't have corresponding uploads
            required_types = DocumentType.objects.filter(
                application=user.application,
                is_required=True
            )
            
            for doc_type in required_types:
                # Check if this document type has been uploaded
                has_document = DocumentStage.objects.filter(
                    loan_application=loan_application,
                    category=doc_type.category
                ).exists()
                
                if not has_document:
                    missing_documents.append({
                        'category': doc_type.category.category_name,
                        'type': doc_type.type_name,
                        'description': doc_type.description
                    })
        
        # Generate letter content based on type
        content = generate_letter_content(
            letter_type, 
            loan_application, 
            missing_documents
        )
        
        # In a real implementation, you would save the letter to the database
        # and possibly generate a PDF
        
        return Response({
            'letter_type': letter_type,
            'loan_id': str(loan_id),
            'applicant_name': loan_application.applicant_name,
            'generated_at': timezone.now().isoformat(),
            'content': content
        })
    except LoanApplication.DoesNotExist:
        return Response(
            {'error': 'Loan application not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )


def generate_letter_content(letter_type, loan_application, missing_documents=None):
    """
    Generate letter content based on type and loan application data
    """
    # In a real implementation, you would use Together AI or another LLM
    # to generate personalized letter content
    
    applicant_name = loan_application.applicant_name
    loan_amount = f"${loan_application.loan_amount:,.2f}"
    loan_purpose = loan_application.loan_purpose
    
    if letter_type == 'WELCOME':
        return f"""
Dear {applicant_name},

Thank you for choosing our institution for your {loan_purpose} loan application of {loan_amount}. We are excited to work with you on this journey.

Our team will review your application and reach out if we need any additional information. You can track the status of your application and upload documents through our online portal.

Best regards,
The Loan Team
"""
    
    elif letter_type == 'STATUS_UPDATE':
        status = loan_application.get_application_status_display()
        return f"""
Dear {applicant_name},

We wanted to provide you with an update on your {loan_purpose} loan application of {loan_amount}.

Your application is currently in {status} status. Our team is working diligently to process your application as quickly as possible.

You can track the status of your application and upload any required documents through our online portal.

Best regards,
The Loan Team
"""
    
    elif letter_type == 'DOCUMENT_REQUEST':
        docs_list = "\n".join([f"- {doc['category']}: {doc['type']} ({doc['description']})" for doc in (missing_documents or [])])
        return f"""
Dear {applicant_name},

We are currently processing your {loan_purpose} loan application of {loan_amount}. To proceed further, we need the following documents:

{docs_list}

Please upload these documents through our online portal at your earliest convenience.

Best regards,
The Loan Team
"""
    
    elif letter_type == 'APPROVAL':
        return f"""
Dear {applicant_name},

Congratulations! We are pleased to inform you that your {loan_purpose} loan application of {loan_amount} has been approved.

Our team will contact you shortly to discuss the next steps and finalize the details.

Best regards,
The Loan Team
"""
    
    elif letter_type == 'REJECTION':
        return f"""
Dear {applicant_name},

Thank you for your {loan_purpose} loan application of {loan_amount}.

After careful review, we regret to inform you that we are unable to approve your loan application at this time. Please contact our office if you would like to discuss the specific reasons or explore alternative options.

Best regards,
The Loan Team
"""
    
    else:
        return "Letter content not available."


# ===============================================
# Dashboard and Metrics APIs
# ===============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def loan_application_metrics(request, loan_id):
    """
    Get metrics for a specific loan application
    """
    user = request.user
    
    try:
        loan_application = LoanApplication.objects.get(id=loan_id)
        
        # Check if user has permission to view this loan
        if user.role and user.role.name in ['CEO', 'CTO', 'Admin', 'Loan Officer']:
            # Admin users can view any loan
            pass
        elif loan_application.user != user:
            return Response(
                {'error': 'You do not have permission to view this loan application'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get or calculate metrics
        case_readiness = loan_application.case_readiness
        document_index = loan_application.document_index
        dti_ratio = loan_application.dti_ratio or 0
        credit_score = loan_application.credit_score or 0
        
        # Get document counts by category
        documents_by_category = DocumentStage.objects.filter(
            loan_application=loan_application
        ).values('category__category_name').annotate(
            count=Count('id')
        )
        
        # Get document counts by status
        documents_by_status = DocumentStage.objects.filter(
            loan_application=loan_application
        ).values('status').annotate(
            count=Count('id')
        )
        
        # Get missing required documents
        required_types = DocumentType.objects.filter(
            application=user.application,
            is_required=True
        )
        
        missing_documents = []
        for doc_type in required_types:
            # Check if this document type has been uploaded
            has_document = DocumentStage.objects.filter(
                loan_application=loan_application,
                category=doc_type.category
            ).exists()
            
            if not has_document:
                missing_documents.append({
                    'category': doc_type.category.category_name,
                    'type': doc_type.type_name,
                    'description': doc_type.description
                })
        
        return Response({
            'loan_id': str(loan_id),
            'metrics': {
                'case_readiness': case_readiness,
                'document_index': document_index,
                'dti_ratio': dti_ratio,
                'credit_score': credit_score
            },
            'documents': {
                'by_category': documents_by_category,
                'by_status': documents_by_status,
                'missing_required': missing_documents
            }
        })
    except LoanApplication.DoesNotExist:
        return Response(
            {'error': 'Loan application not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    

# Add this to your views.py file

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def loan_documents(request, loan_id):
    """
    Get documents for a specific loan application, organized by categories
    """
    try:
        # Validate that loan exists and user has access
        loan_application = LoanApplication.objects.get(id=loan_id)
        
        # Check if user has permission to view this loan
        if not (request.user.role and request.user.role.name in ['CEO', 'CTO', 'Admin', 'Loan Officer']) and loan_application.user != request.user:
            return Response(
                {'error': 'You do not have permission to view documents for this loan application'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get all document categories from the system
        all_categories = DocumentCategory.objects.filter(
            application=request.user.application
        ).order_by('order')
        
        # Get all documents for this loan application
        loan_documents = DocumentStage.objects.filter(
            loan_application=loan_application
        )
        
        # Organize documents by category
        result = []
        for category in all_categories:
            category_docs = loan_documents.filter(category=category)
            
            # Skip categories with no documents, except for required ones
            if not category_docs and category.document_types.filter(is_required=True).count() == 0:
                continue
                
            category_data = {
                'id': str(category.id),
                'name': category.category_name,
                'code': category.category_code,
                'documents': []
            }
            
            # Add documents for this category
            for doc in category_docs:
                category_data['documents'].append({
                    'id': str(doc.id),
                    'name': doc.document_name,
                    'status': doc.status,
                    'uploaded_at': doc.uploaded_at,
                    'metadata': doc.metadata
                })
            
            result.append(category_data)
        
        return Response(result)
    except LoanApplication.DoesNotExist:
        return Response(
            {'error': 'Loan application not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )