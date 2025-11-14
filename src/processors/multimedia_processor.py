import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import pypdf
from docx import Document as DocxDocument
import base64 # Import base64 for image/video encoding
import io # Import io for image handling
import asyncio # Import asyncio for async calls
from src.processors.video_audio_processor import VideoAudioProcessor # Import the new processor

# Optional imports with fallbacks
try:
    import pytesseract
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps
    OCR_AVAILABLE = True
except ImportError:
    pytesseract = None
    Image = ImageEnhance = ImageFilter = ImageOps = None
    OCR_AVAILABLE = False

try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    convert_from_path = None
    PDF2IMAGE_AVAILABLE = False

class MultimediaProcessor:
    def __init__(self):
        self.supported_formats = {
            'text': ['.pdf', '.docx', '.txt', '.md'],
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp'],
            'audio': ['.mp3', '.wav', '.m4a', '.ogg'],
            'video': ['.mp4', '.avi', '.mov', '.mkv', '.webm']
        }
        self._cache = {}  # Simple file processing cache
        self.video_audio_processor = VideoAudioProcessor() # Initialize the new processor
    
    async def process_file(self, file_path: str) -> Dict[str, Any]:
        """Process any supported file type and extract relevant information"""
        
        file_extension = Path(file_path).suffix.lower()
        file_type = self._get_file_type(file_extension)
        
        result = {
            'filename': Path(file_path).name,
            'file_path': file_path,
            'file_type': file_type,
            'extension': file_extension,
            'size': 0, # Initialize size to 0, update in try block
            'content': '',
            'metadata': {},
            'description': '',
            'base64_image': None,
            'base64_video_frames': []
        }
        
        try:
            # Check file existence and get mtime for caching
            if not Path(file_path).exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            file_size = os.path.getsize(file_path)
            result['size'] = file_size
            cache_key = f"{file_path}_{os.path.getmtime(file_path)}"
            
            if cache_key in self._cache:
                print(f"DEBUG: Using cached result for file: {file_path}")
                return self._cache[cache_key]

            print(f"DEBUG: Starting processing for file: {file_path} (Type: {file_type})")
            if file_type == 'text':
                result['content'] = self._extract_text(file_path)
                result['description'] = self._generate_text_description(result['content'])
            elif file_type == 'image':
                extracted_text = self._extract_text_from_image(file_path)
                result['content'] = extracted_text if extracted_text else f"Image file: {Path(file_path).name}"
                result['description'] = self._generate_image_description(file_path)
                result['base64_image'] = self._image_to_base64(file_path)
            elif file_type == 'audio':
                transcription = await self.video_audio_processor.transcribe_audio_file(file_path)
                result['content'] = transcription if transcription else f"Audio file: {Path(file_path).name}"
                result['description'] = self._generate_audio_description(file_path, transcription)
            elif file_type == 'video':
                video_processing_result = await self.video_audio_processor.process_video(file_path)
                result['content'] = video_processing_result['content'] if video_processing_result['content'] else f"Video file: {Path(file_path).name}"
                result['description'] = self._generate_video_description(file_path, video_processing_result['content'])
                result['base64_video_frames'] = video_processing_result['base64_video_frames']
            else:
                result['description'] = f"Unsupported file type: {file_extension}"
            print(f"DEBUG: Finished processing for file: {file_path}. Content length: {len(result['content'])} chars.")
            
            # Cache the result only if processing was successful
            self._cache[cache_key] = result
            
        except FileNotFoundError as e:
            print(f"ERROR: File not found during processing for {file_path}: {e}")
            result['description'] = f"Error: File not found - {str(e)}"
            result['content'] = f"Could not process file: File not found."
        except Exception as e:
            print(f"ERROR: Exception during file processing for {file_path}: {e}")
            result['description'] = f"Error processing file: {str(e)}"
            result['content'] = f"Could not process file due to an error: {str(e)}"
        
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
            elif file_extension in ['.txt', '.md']:
                # Try different encodings
                for encoding in ['utf-8', 'utf-16', 'latin-1', 'cp1252']:
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            content = f.read()
                            # Limit content size to prevent memory issues
                            max_text_content_size = 200000 # ~200KB limit
                            if len(content) > max_text_content_size:
                                print(f"Warning: Text content from {file_path} truncated. Original size: {len(content)} chars.")
                                content = content[:max_text_content_size] + "\n[Content truncated due to size]"
                            return content
                    except UnicodeDecodeError:
                        print(f"DEBUG: Failed to decode {file_path} with encoding {encoding}")
                        continue
                print(f"Error: Could not decode text file {file_path} with any supported encoding.")
                return "Could not decode file with any supported encoding"
            else:
                print(f"Warning: Attempted to extract text from unsupported extension {file_extension} for file {file_path}.")
                return ""
        except Exception as e:
            print(f"Error extracting text from {file_path}: {e}")
            return f"Error extracting text: {str(e)}"
        
        return ""
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                # Limit pages to prevent memory issues
                max_pages_to_process = 50
                max_text_content_size = 200000 # ~200KB limit
                
                num_pages = len(pdf_reader.pages)
                if num_pages > max_pages_to_process:
                    print(f"Warning: PDF {file_path} has {num_pages} pages, processing only first {max_pages_to_process}.")

                for i in range(min(num_pages, max_pages_to_process)):
                    page_text = pdf_reader.pages[i].extract_text()
                    text += page_text + "\n"
                    # Stop if content gets too large
                    if len(text) > max_text_content_size:
                        print(f"Warning: PDF content from {file_path} truncated. Original size: {len(text)} chars.")
                        text += "\n[Content truncated - file too large]"
                        break
            
            # Always attempt OCR if available, and combine with direct text extraction
            if PDF2IMAGE_AVAILABLE and OCR_AVAILABLE:
                print(f"DEBUG: Attempting OCR for PDF {file_path}.")
                try:
                    images = convert_from_path(file_path, first_page=1, last_page=min(num_pages, max_pages_to_process), dpi=200) # Increased DPI for better OCR
                    ocr_texts = []
                    for i, img in enumerate(images):
                        # Pass the PIL Image object directly to _extract_text_from_image
                        # Ensure the image is in a format that pytesseract can handle (e.g., RGB or L)
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        ocr_page_text = self._extract_text_from_image(img)
                        if ocr_page_text and ocr_page_text.strip() not in ["No text detected in image", "Image contains minimal or no readable text", "OCR failed: "]:
                            ocr_texts.append(f"--- OCR Page {i+1} ---\n{ocr_page_text}")
                    
                    if ocr_texts:
                        combined_ocr_text = "\n".join(ocr_texts)
                        # Combine direct text and OCR text, avoiding obvious duplicates
                        if text.strip() and combined_ocr_text.strip():
                            # Simple heuristic to combine: if direct text is very short, prioritize OCR.
                            # Otherwise, append OCR text to direct text.
                            if len(text.strip()) < 100: # Arbitrary threshold for "very short"
                                text = f"{combined_ocr_text}\n\n{text}"
                            else:
                                text = f"{text}\n\n{combined_ocr_text}"
                            print(f"DEBUG: Combined direct and OCR text for {file_path}.")
                        elif combined_ocr_text.strip():
                            text = combined_ocr_text
                            print(f"DEBUG: Used only OCR text for {file_path} as direct text was empty.")
                    else:
                        print(f"DEBUG: No significant OCR text extracted for {file_path}.")
                except Exception as ocr_e:
                    print(f"ERROR: OCR processing failed for PDF {file_path}: {ocr_e}")
                    text += f"\n[Warning: OCR failed for this PDF: {ocr_e}]"
            else:
                print(f"DEBUG: OCR or PDF2Image not available for {file_path}. Skipping OCR.")

            return text.strip()
        except Exception as e:
            print(f"ERROR: Error reading PDF {file_path}: {e}")
            return f"Error reading PDF: {str(e)}"
    
    def _extract_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            doc = DocxDocument(file_path)
            text = ""
            max_text_content_size = 200000 # ~200KB limit
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
                if len(text) > max_text_content_size:
                    print(f"Warning: DOCX content from {file_path} truncated. Original size: {len(text)} chars.")
                    text += "\n[Content truncated - file too large]"
                    break
            return text.strip()
        except Exception as e:
            print(f"Error reading DOCX {file_path}: {e}")
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
        """Generate description for image files with enhanced OCR text extraction"""
        try:
            # Try OCR text extraction first
            extracted_text = self._extract_text_from_image(file_path)
            
            with Image.open(file_path) as img:
                width, height = img.size
                format_name = img.format
                file_size = os.path.getsize(file_path) / 1024  # KB
                
                description = f"Image file ({format_name}) - {width}x{height} pixels ({file_size:.1f}KB)."
                
                if extracted_text and not extracted_text.startswith(("OCR", "No text", "Image contains")):
                    word_count = len(extracted_text.split())
                    description += f" Contains {word_count} words of text: {extracted_text[:150]}{'...' if len(extracted_text) > 150 else ''}"
                elif extracted_text:
                    description += f" {extracted_text}"
                else:
                    description += " Visual content ready for analysis."
                    
                return description
                
        except ImportError:
            return f"Image file - {Path(file_path).name}. Install Pillow and pytesseract for text extraction."
        except Exception as e:
            return f"Image file - {Path(file_path).name}. Analysis error: {str(e)}"
    
    def _generate_video_description(self, file_path: str, video_content: str) -> str:
        """Generate description for video files with frame extraction"""
        try:
            file_size = os.path.getsize(file_path)
            size_mb = file_size / (1024 * 1024)
            
            description = f"Video file - {Path(file_path).name} ({size_mb:.1f}MB)."
            
            if video_content and len(video_content.strip()) > 10:
                word_count = len(video_content.split())
                description += f" Extracted text from frames and audio ({word_count} words): {video_content[:200]}{'...' if len(video_content) > 200 else ''}"
            else:
                description += " Video processed, no readable text found in frames or audio."
                
            return description
        except Exception as e:
            return f"Video file - {Path(file_path).name}. Could not analyze: {str(e)}"
    
    def _generate_audio_description(self, file_path: str, transcription: str) -> str:
        """Generate description for audio files with transcription"""
        try:
            file_size = os.path.getsize(file_path)
            size_mb = file_size / (1024 * 1024)
            
            description = f"Audio file - {Path(file_path).name} ({size_mb:.1f}MB)."
            
            if transcription and not transcription.startswith("Audio transcription"):
                word_count = len(transcription.split())
                description += f" Transcribed {word_count} words: {transcription[:200]}{'...' if len(transcription) > 200 else ''}"
            else:
                description += " Audio transcription not available."
                
            return description
        except Exception as e:
            return f"Audio file - {Path(file_path).name}. Could not analyze: {str(e)}"
    
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
    
    def _image_to_base64(self, image_input: Any, max_size_kb: int = 1024) -> Optional[str]:
        """Converts an image (file path or PIL Image) to a base64 string, resizing if necessary."""
        if not Image:
            return None
        
        img = None
        if isinstance(image_input, str): # It's a file path
            try:
                img = Image.open(image_input)
            except Exception as e:
                print(f"Error opening image file {image_input}: {e}")
                return None
        elif isinstance(image_input, Image.Image): # It's a PIL Image object
            img = image_input
        else:
            print(f"Invalid image_input type: {type(image_input)}")
            return None

        try:
            # Convert to RGB if necessary (some models prefer RGB)
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Check size and resize if too large
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG')
            
            # Initial check
            if img_byte_arr.tell() > max_size_kb * 1024:
                # Resize logic: aim for a smaller dimension while maintaining aspect ratio
                # and re-check size. Iterate if needed.
                quality = 90
                # Keep resizing until it fits or quality is too low
                while img_byte_arr.tell() > max_size_kb * 1024 and quality >= 30: # Don't go below 30 quality
                    width, height = img.size
                    # Reduce dimensions by a factor, then try reducing quality
                    if img_byte_arr.tell() > max_size_kb * 1024 * 2: # If still very large, reduce size more aggressively
                        scale_factor = 0.7
                    else:
                        scale_factor = 0.9
                    new_size = (int(width * scale_factor), int(height * scale_factor))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                    
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format='JPEG', quality=quality)
                    quality -= 10 # Reduce quality for next iteration

            return base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
        except Exception as e:
            print(f"Error converting image to base64: {e}")
            return None
    
    def _extract_text_from_image(self, image_input: Any) -> str: # Changed parameter name to image_input
        """Extract text from image using OCR with enhanced preprocessing"""
        if not OCR_AVAILABLE:
            return "OCR not available - install pytesseract and tesseract"
        
        try:
            img = None
            if isinstance(image_input, str): # It's a file path
                img = Image.open(image_input)
            elif isinstance(image_input, Image.Image): # It's a PIL Image object
                img = image_input
            else:
                return "Invalid image input type for OCR"

            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize if image is too small or too large for optimal OCR
            width, height = img.size
            # Aim for a target DPI, e.g., 300 DPI for OCR. If original image is low res, upscale.
            # Assuming 96 DPI as a common screen DPI for calculation.
            target_dpi = 300
            current_dpi = img.info.get('dpi', (96, 96))[0] # Get DPI from image info, default to 96
            
            if current_dpi < target_dpi:
                scale_factor = target_dpi / current_dpi
                new_size = (int(width * scale_factor), int(height * scale_factor))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                width, height = img.size # Update width, height after resize

            # Further resize if image is still too small or too large after DPI adjustment
            if width < 600 or height < 600: # Minimum reasonable size for good OCR
                scale_factor = max(600/width, 600/height)
                new_size = (int(width * scale_factor), int(height * scale_factor))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            elif width > 4000 or height > 4000: # Max reasonable size to prevent memory issues
                scale_factor = min(4000/width, 4000/height)
                new_size = (int(width * scale_factor), int(height * scale_factor))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Convert to grayscale for better OCR
            img = img.convert('L')
            
            # Apply noise reduction (more aggressive)
            img = img.filter(ImageFilter.MedianFilter(size=5)) # Increased filter size
            
            # Enhance contrast and sharpness (more aggressive)
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(2.0) # Increased enhancement factor
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.5) # Increased enhancement factor
            
            # Apply threshold to create binary image
            img = ImageOps.autocontrast(img)
            
            # Try multiple OCR configurations
            configs = [
                r'--oem 3 --psm 6',  # Assume a single uniform block of text.
                r'--oem 3 --psm 3',  # Default, based on page layout analysis.
                r'--oem 3 --psm 1',  # Automatic page segmentation with OSD.
                r'--oem 3 --psm 11', # Sparse text. Find as much text as possible in no particular order.
                r'--oem 3 --psm 12', # Raw line. Treat the image as a single text line.
            ]
            
            best_text = ""
            for config in configs:
                try:
                    extracted_text = pytesseract.image_to_string(img, config=config)
                    if len(extracted_text.strip()) > len(best_text.strip()):
                        best_text = extracted_text
                except Exception as e:
                    print(f"OCR config '{config}' failed: {e}")
                    continue
            
            # Clean up extracted text
            if best_text:
                lines = [line.strip() for line in best_text.split('\n') if line.strip()]
                cleaned_text = '\n'.join(lines)
                
                # Filter out very short or nonsensical results
                if len(cleaned_text.strip()) < 5: # Increased minimum length
                    return "Image contains minimal or no readable text"
                
                return cleaned_text
            else:
                return "No text detected in image"
                
        except ImportError:
            return "OCR dependencies missing"
        except Exception as e:
            print(f"OCR extraction failed for {image_input}: {e}")
            return f"OCR failed: {str(e)}"
