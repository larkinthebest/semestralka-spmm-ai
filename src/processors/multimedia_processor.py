import os
from pathlib import Path
from typing import Optional, Dict, Any
import PyPDF2
from docx import Document as DocxDocument

class MultimediaProcessor:
    def __init__(self):
        self.supported_formats = {
            'text': ['.pdf', '.docx', '.txt'],
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp'],
            'audio': ['.mp3', '.wav', '.m4a', '.ogg'],
            'video': ['.mp4', '.avi', '.mov', '.mkv', '.webm']
        }
    
    def process_file(self, file_path: str) -> Dict[str, Any]:
        """Process any supported file type and extract relevant information"""
        file_extension = Path(file_path).suffix.lower()
        file_type = self._get_file_type(file_extension)
        
        result = {
            'filename': Path(file_path).name,
            'file_path': file_path,
            'file_type': file_type,
            'extension': file_extension,
            'size': os.path.getsize(file_path),
            'content': '',
            'metadata': {},
            'description': ''
        }
        
        if file_type == 'text':
            result['content'] = self._extract_text(file_path)
            result['description'] = self._generate_text_description(result['content'])
        elif file_type == 'image':
            result['description'] = self._generate_image_description(file_path)
        elif file_type == 'audio':
            result['description'] = self._generate_audio_description(file_path)
        elif file_type == 'video':
            result['description'] = self._generate_video_description(file_path)
        else:
            result['description'] = f"Unsupported file type: {file_extension}"
        
        return result
    
    def _get_file_type(self, extension: str) -> str:
        """Determine file type based on extension"""
        for file_type, extensions in self.supported_formats.items():
            if extension in extensions:
                return file_type
        return 'unknown'
    
    def _extract_text(self, file_path: str) -> str:
        """Extract text from text-based files"""
        file_extension = Path(file_path).suffix.lower()
        
        try:
            if file_extension == '.pdf':
                return self._extract_from_pdf(file_path)
            elif file_extension == '.docx':
                return self._extract_from_docx(file_path)
            elif file_extension == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            return f"Error extracting text: {str(e)}"
        
        return ""
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            return f"Error reading PDF: {str(e)}"
    
    def _extract_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            doc = DocxDocument(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            return f"Error reading DOCX: {str(e)}"
    
    def _generate_text_description(self, content: str) -> str:
        """Generate a brief description of text content"""
        if not content or len(content.strip()) == 0:
            return "Empty or unreadable text document"
        
        # Get first few sentences or words
        words = content.split()
        if len(words) > 50:
            preview = ' '.join(words[:50]) + "..."
        else:
            preview = content
        
        word_count = len(words)
        return f"Text document with {word_count} words. Preview: {preview}"
    
    def _generate_image_description(self, file_path: str) -> str:
        """Generate description for image files"""
        try:
            from PIL import Image
            with Image.open(file_path) as img:
                width, height = img.size
                format_name = img.format
                return f"Image file ({format_name}) - {width}x{height} pixels. Ready for visual analysis."
        except ImportError:
            return f"Image file - {Path(file_path).name}. Install Pillow for detailed image analysis."
        except Exception as e:
            return f"Image file - {Path(file_path).name}. Could not analyze: {str(e)}"
    
    def _generate_audio_description(self, file_path: str) -> str:
        """Generate description for audio files"""
        try:
            # Try to get basic audio info
            file_size = os.path.getsize(file_path)
            size_mb = file_size / (1024 * 1024)
            return f"Audio file - {Path(file_path).name} ({size_mb:.1f}MB). Ready for audio analysis and transcription."
        except Exception as e:
            return f"Audio file - {Path(file_path).name}. Could not analyze: {str(e)}"
    
    def _generate_video_description(self, file_path: str) -> str:
        """Generate description for video files"""
        try:
            file_size = os.path.getsize(file_path)
            size_mb = file_size / (1024 * 1024)
            return f"Video file - {Path(file_path).name} ({size_mb:.1f}MB). Ready for video analysis and frame extraction."
        except Exception as e:
            return f"Video file - {Path(file_path).name}. Could not analyze: {str(e)}"
    
    def get_content_summary(self, file_info: Dict[str, Any]) -> str:
        """Get a summary of the file content for AI context"""
        file_type = file_info.get('file_type', 'unknown')
        filename = file_info.get('filename', 'unknown')
        description = file_info.get('description', '')
        content = file_info.get('content', '')
        
        summary = f"File: {filename} (Type: {file_type})\n"
        summary += f"Description: {description}\n"
        
        if content and len(content.strip()) > 0:
            # Include first part of content for context
            words = content.split()
            if len(words) > 100:
                content_preview = ' '.join(words[:100]) + "..."
            else:
                content_preview = content
            summary += f"Content preview: {content_preview}\n"
        
        return summary