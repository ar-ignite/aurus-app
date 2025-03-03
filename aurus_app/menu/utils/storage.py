import os
import uuid
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import os
import PyPDF2
import docx
from PIL import Image
import pytesseract
import requests
import json

class DocumentStorage:
    """Utility class for handling document storage operations"""
    @staticmethod
    def read_document(document_path):
        """
        Read a document file and return its content
        
        Args:
            document_path: Path to the document file
            
        Returns:
            str: The text content of the document
        """
        try:
            # Get the full path to the file
            file_path = os.path.join(settings.MEDIA_ROOT, document_path)
            
            # Get file extension
            _, file_extension = os.path.splitext(document_path)
            file_extension = file_extension.lower()
            
            # Process based on file type
            if file_extension == '.pdf':
                return extract_text_from_pdf(file_path)
            elif file_extension in ['.docx', '.doc']:
                return extract_text_from_word(file_path)
            elif file_extension in ['.jpg', '.jpeg', '.png']:
                return extract_text_from_image(file_path)
            else:
                return f"Unsupported file type: {file_extension}"
                
        except Exception as e:
            print(f"Error reading document: {e}")
            return f"Error extracting text: {str(e)}"
        
    @staticmethod
    def save_document(uploaded_file, document_type):
        """
        Save an uploaded document to the appropriate storage location
        
        Args:
            uploaded_file: The file object from request.FILES
            document_type: The type of document (used for folder organization)
            
        Returns:
            str: The relative path where the file was saved
        """
        # Generate a unique filename to prevent collisions
        file_extension = os.path.splitext(uploaded_file.name)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # Create a directory structure based on document type
        relative_path = f"documents/{document_type.lower()}/{unique_filename}"
        
        # Use Django's FileSystemStorage to save the file
        fs = FileSystemStorage()
        file_path = fs.save(relative_path, uploaded_file)
        
        return file_path

    @staticmethod
    def delete_document(document_path):
        """
        Delete a document from storage
        
        Args:
            document_path: The relative path of the document
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        if not document_path:
            return False
            
        fs = FileSystemStorage()
        try:
            if fs.exists(document_path):
                fs.delete(document_path)
                return True
        except Exception as e:
            # Log the error
            print(f"Error deleting document: {e}")
        
        return False


def extract_text_from_pdf(file_path):
    """Extract text from PDF file"""
    text = ""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""


def extract_text_from_word(file_path):
    """Extract text from Word document"""
    try:
        doc = docx.Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    except Exception as e:
        print(f"Error extracting text from Word: {e}")
        return ""


def extract_text_from_image(file_path):
    """Extract text from image using OCR"""
    try:
        img = Image.open(file_path)
        text = pytesseract.image_to_string(img)
        return text
    except Exception as e:
        print(f"Error extracting text from image: {e}")
        return ""