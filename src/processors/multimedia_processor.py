import os
from pathlib import Path
from typing import Optional, Dict, Any
import PyPDF2
from docx import Document as DocxDocument

# Optional imports with fallbacks
try:
    import pytesseract
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps
    import numpy as np
    OCR_AVAILABLE = True
except ImportError:
    pytesseract = None
    Image = ImageEnhance = ImageFilter = ImageOps = np = None
    OCR_AVAILABLE = False

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    whisper = None
    WHISPER_AVAILABLE = False

try:
    import cv2
    import tempfile
    CV2_AVAILABLE = True
except ImportError:
    cv2 = None
    CV2_AVAILABLE = False

class MultimediaProcessor:
    def __init__(self):
        self.supported_formats = {
            'text': ['.pdf', '.docx', '.txt', '.md'],
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp'],
            'audio': ['.mp3', '.wav', '.m4a', '.ogg'],
            'video': ['.mp4', '.avi', '.mov', '.mkv', '.webm']
        }
        self._cache = {}  # Simple file processing cache
    
    def process_file(self, file_path: str) -> Dict[str, Any]:
        """Process any supported file type and extract relevant information"""
        # Check cache first
        cache_key = f"{file_path}_{os.path.getmtime(file_path)}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        file_extension = Path(file_path).suffix.lower()
        file_type = self._get_file_type(file_extension)
        
        try:
            file_size = os.path.getsize(file_path)
        except OSError:
            file_size = 0
        
        result = {
            'filename': Path(file_path).name,
            'file_path': file_path,
            'file_type': file_type,
            'extension': file_extension,
            'size': file_size,
            'content': '',
            'metadata': {},
            'description': ''
        }
        
        try:
            if file_type == 'text':
                result['content'] = self._extract_text(file_path)
                result['description'] = self._generate_text_description(result['content'])
            elif file_type == 'image':
                # Extract text from image and include in content
                extracted_text = self._extract_text_from_image(file_path)
                result['content'] = extracted_text if extracted_text else f"Image file: {Path(file_path).name}"
                result['description'] = self._generate_image_description(file_path)
            elif file_type == 'audio':
                transcription = self._transcribe_audio(file_path)
                result['content'] = transcription if transcription else f"Audio file: {Path(file_path).name}"
                result['description'] = self._generate_audio_description(file_path)
            elif file_type == 'video':
                video_text = self._extract_video_text(file_path)
                result['content'] = video_text if video_text else f"Video file: {Path(file_path).name}"
                result['description'] = self._generate_video_description(file_path)
            else:
                result['description'] = f"Unsupported file type: {file_extension}"
        except Exception as e:
            result['description'] = f"Error processing file: {str(e)}"
            result['content'] = f"Could not process file: {str(e)}"
        
        # Cache the result
        self._cache[cache_key] = result
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
                            if len(content) > 200000:  # ~200KB limit
                                content = content[:200000] + "\n[Content truncated due to size]"
                            return content
                    except UnicodeDecodeError:
                        continue
                return "Could not decode file with any supported encoding"
        except Exception as e:
            return f"Error extracting text: {str(e)}"
        
        return ""
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                # Limit pages to prevent memory issues
                max_pages = min(len(pdf_reader.pages), 50)
                for i in range(max_pages):
                    page_text = pdf_reader.pages[i].extract_text()
                    text += page_text + "\n"
                    # Stop if content gets too large
                    if len(text) > 200000:
                        text += "\n[Content truncated - file too large]"
                        break
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
        """Generate description for image files with enhanced OCR text extraction"""
        try:
            from PIL import Image
            
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
    
    def _generate_video_description(self, file_path: str) -> str:
        """Generate description for video files with frame extraction"""
        try:
            file_size = os.path.getsize(file_path)
            size_mb = file_size / (1024 * 1024)
            
            video_text = self._extract_video_text(file_path)
            
            description = f"Video file - {Path(file_path).name} ({size_mb:.1f}MB)."
            
            if video_text and len(video_text.strip()) > 10:
                word_count = len(video_text.split())
                description += f" Extracted text from frames ({word_count} words): {video_text[:200]}{'...' if len(video_text) > 200 else ''}"
            else:
                description += " Video processed, no readable text found in frames."
                
            return description
        except Exception as e:
            return f"Video file - {Path(file_path).name}. Could not analyze: {str(e)}"
    
    def _generate_audio_description(self, file_path: str) -> str:
        """Generate description for audio files with transcription"""
        try:
            file_size = os.path.getsize(file_path)
            size_mb = file_size / (1024 * 1024)
            
            transcription = self._transcribe_audio(file_path)
            
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
    
    def _extract_text_from_image(self, file_path: str) -> str:
        """Extract text from image using OCR with enhanced preprocessing"""
        if not OCR_AVAILABLE:
            return "OCR not available - install pytesseract and tesseract"
        
        try:
            
            # Open and preprocess image for better OCR
            with Image.open(file_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize if image is too small or too large
                width, height = img.size
                if width < 300 or height < 300:
                    # Upscale small images
                    scale_factor = max(300/width, 300/height)
                    new_size = (int(width * scale_factor), int(height * scale_factor))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                elif width > 3000 or height > 3000:
                    # Downscale very large images
                    scale_factor = min(3000/width, 3000/height)
                    new_size = (int(width * scale_factor), int(height * scale_factor))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # Convert to grayscale for better OCR
                img = img.convert('L')
                
                # Apply noise reduction
                img = img.filter(ImageFilter.MedianFilter(size=3))
                
                # Enhance contrast and sharpness
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.5)
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(1.2)
                
                # Apply threshold to create binary image
                img = ImageOps.autocontrast(img)
                
                # Try multiple OCR configurations
                configs = [
                    r'--oem 3 --psm 6',  # Uniform block of text
                    r'--oem 3 --psm 3',  # Fully automatic page segmentation
                    r'--oem 3 --psm 1',  # Automatic page segmentation with OSD
                    r'--oem 3 --psm 11', # Sparse text
                ]
                
                best_text = ""
                for config in configs:
                    try:
                        extracted_text = pytesseract.image_to_string(img, config=config)
                        if len(extracted_text.strip()) > len(best_text.strip()):
                            best_text = extracted_text
                    except Exception:
                        continue
                
                # Clean up extracted text
                if best_text:
                    lines = [line.strip() for line in best_text.split('\n') if line.strip()]
                    cleaned_text = '\n'.join(lines)
                    
                    # Filter out very short or nonsensical results
                    if len(cleaned_text.strip()) < 3:
                        return "Image contains minimal or no readable text"
                    
                    return cleaned_text
                else:
                    return "No text detected in image"
                
        except ImportError:
            return "OCR dependencies missing"
        except Exception as e:
            print(f"OCR extraction failed for {file_path}: {e}")
            return f"OCR failed: {str(e)}"
    
    def _transcribe_audio(self, file_path: str) -> str:
        """Transcribe audio using Whisper with full unlimited transcription"""
        if not WHISPER_AVAILABLE:
            return "Whisper not available"
        
        try:
            model = whisper.load_model("base")  # Use base model for better accuracy
            result = model.transcribe(
                file_path, 
                language=None, 
                task="transcribe",
                verbose=False,
                word_timestamps=True  # Enable word-level timestamps
            )
            
            # Build full transcription with timestamps
            if "segments" in result:
                transcription_parts = []
                for segment in result["segments"]:
                    start_time = segment.get("start", 0)
                    text = segment["text"].strip()
                    if text:
                        # Format timestamp as [MM:SS]
                        minutes = int(start_time // 60)
                        seconds = int(start_time % 60)
                        timestamp = f"[{minutes:02d}:{seconds:02d}]"
                        transcription_parts.append(f"{timestamp} {text}")
                
                return "\n".join(transcription_parts)
            else:
                return result["text"].strip()
            
        except ImportError:
            return "Audio transcription not available"
        except Exception as e:
            print(f"Audio transcription failed: {e}")
            return f"Audio transcription failed: {str(e)}"
    
    def _extract_video_text(self, file_path: str) -> str:
        """Extract text from video frames using OCR and transcribe audio track"""
        if not CV2_AVAILABLE:
            return ""
        
        try:
            cap = cv2.VideoCapture(file_path)
            if not cap.isOpened():
                return ""
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0
            
            # Extract more frames for better coverage (every 5 seconds or 50 frames total)
            frame_interval = max(int(fps * 5), 1) if fps > 0 else max(total_frames // 50, 1)
            max_frames = 50  # Process up to 50 frames
            
            frame_texts = []
            frame_count = 0
            processed_frames = 0
            
            while frame_count < total_frames and processed_frames < max_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_count % frame_interval == 0:
                    timestamp = frame_count / fps if fps > 0 else 0
                    minutes = int(timestamp // 60)
                    seconds = int(timestamp % 60)
                    
                    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                        cv2.imwrite(temp_file.name, frame)
                        
                        if OCR_AVAILABLE:
                            frame_text = self._extract_text_from_image(temp_file.name)
                            if frame_text and len(frame_text.strip()) > 10 and not frame_text.startswith(("OCR", "No text", "Image")):
                                frame_texts.append(f"[{minutes:02d}:{seconds:02d}] {frame_text.strip()}")
                        
                        os.unlink(temp_file.name)
                    
                    processed_frames += 1
                
                frame_count += 1
            
            cap.release()
            
            # Extract audio and transcribe
            audio_transcription = ""
            if WHISPER_AVAILABLE:
                try:
                    # Extract audio from video
                    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
                        audio_path = temp_audio.name
                    
                    # Use ffmpeg via cv2 to extract audio (if available)
                    import subprocess
                    try:
                        subprocess.run(
                            ['ffmpeg', '-i', file_path, '-vn', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1', audio_path],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            timeout=60
                        )
                        audio_transcription = self._transcribe_audio(audio_path)
                        os.unlink(audio_path)
                    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
                        pass
                except Exception as e:
                    print(f"Audio extraction from video failed: {e}")
            
            # Combine frame text and audio transcription
            result_parts = []
            
            if audio_transcription and len(audio_transcription.strip()) > 20:
                result_parts.append(f"=== AUDIO TRANSCRIPTION ===\n{audio_transcription}")
            
            if frame_texts:
                result_parts.append(f"\n=== TEXT FROM VIDEO FRAMES ===\n" + "\n".join(frame_texts))
            
            return "\n\n".join(result_parts) if result_parts else ""
            
        except ImportError:
            return ""
        except Exception as e:
            print(f"Video text extraction failed: {e}")
            return ""