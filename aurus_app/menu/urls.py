from django.urls import path
from . import views

urlpatterns = [
    # Authentication endpoints
    path('api/users/login/', views.login_view, name='login'),
    # Menu endpoints
    path('api/menu/', views.menu_list, name='menu-list'),
    path('api/documents/upload/', views.document_upload, name='document-upload'),
    path('api/documents/', views.document_list, name='document-list'),
    # Application and client endpoints
    path('api/applications/', views.application_list, name='application-list'),
    path('api/clients/', views.client_list, name='client-list'),
    # Document management endpoints
    path('api/documents/upload/', views.document_upload, name='document-upload'),
    path('api/documents/', views.document_list, name='document-list'),
    path('api/documents/<uuid:document_id>/process/', views.document_process, name='document-process'),
    path('api/documents/<uuid:document_id>/', views.document_delete, name='document-delete'),
    # Health check endpoint for deployment
    path('health/', views.health_check, name='health-check'),

    path('api/menu/user-tree/', views.user_menu_tree, name='user-menu-tree'),
    path('api/roles/', views.all_roles, name='all-roles'),

    # Authentication endpoints (existing)
    path('api/users/login/', views.login_view, name='login'),
    
    # Document upload and processing
    path('api/documents/upload/', views.document_upload, name='document-upload'),
    path('api/documents/<uuid:document_id>/process/', views.process_document_with_ai, name='document-process'),
    
    # Document categories and types
    path('api/document-categories/', views.document_categories, name='document-categories'),
    path('api/document-types/', views.document_types, name='document-types'),
    path('api/document-types/<uuid:category_id>/', views.document_types, name='document-types-by-category'),
    path('api/document-categories/create/', views.create_document_category, name='create-document-category'),
    path('api/document-types/create/', views.create_document_type, name='create-document-type'),
    
    # Document management
    path('api/documents/', views.document_list, name='document-list'),
    path('api/documents/loan/<uuid:loan_application_id>/', views.document_list, name='document-list-by-loan'),
    path('api/documents/<uuid:document_id>/', views.document_details, name='document-details'),
    path('api/documents/<uuid:document_id>/category/', views.update_document_category, name='update-document-category'),
    path('api/documents/<uuid:document_id>/approve-reject/', views.approve_reject_document, name='approve-reject-document'),
    path('api/documents/<uuid:document_id>/delete/', views.delete_document, name='delete-document'),
    
    # Loan applications
    path('api/loans/', views.loan_applications, name='loan-applications'),
    path('api/loans/create/', views.create_loan_application, name='create-loan-application'),
    path('api/loans/<uuid:loan_id>/', views.loan_application_details, name='loan-application-details'),
    path('api/loans/<uuid:loan_id>/update/', views.update_loan_application, name='update-loan-application'),
    path('api/loans/<uuid:loan_id>/submit/', views.submit_loan_application, name='submit-loan-application'),
    path('api/loans/<uuid:loan_id>/process/', views.process_loan_application, name='process-loan-application'),
    
    # AI letter generation
    path('api/loans/<uuid:loan_id>/letter/', views.generate_ai_letter, name='generate-ai-letter'),
    
    # Dashboard and metrics
    path('api/loans/<uuid:loan_id>/metrics/', views.loan_application_metrics, name='loan-application-metrics'),
    
    # Health check endpoint for deployment (existing)
    path('health/', views.health_check, name='health-check'),
    
    # User menu API (existing)
    path('api/menu/user-tree/', views.user_menu_tree, name='user-menu-tree'),
    path('api/roles/', views.all_roles, name='all-roles'),

    path('api/loans/<uuid:loan_id>/documents/', views.loan_documents, name='loan-documents'),

]