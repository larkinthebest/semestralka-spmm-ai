import os
from pathlib import Path
from typing import Optional, List, Dict, Any
import subprocess
import tempfile
import base64
import io

# Optional imports with fallbacks
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    whisper = None
    WHISPER_AVAILABLE = False

try:
    import cv2
    import numpy as np
    from PIL import Image as PILImage # Import PIL.Image as PILImage
    CV2_AVAILABLE = True
except ImportError:
    cv2 = None
    np = None
    PILImage = None # Fallback for PILImage module
    CV2_AVAILABLE = False

try:
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    pytesseract = None
    OCR_AVAILABLE = False

class VideoAudioProcessor:
    def __init__(self):
        self.whisper_model = None # Initialize Whisper model to None

    def _run_ffmpeg_command(self, command: List[str], timeout: int = 300) -> Optional[str]:
        """Helper to run FFmpeg commands with a timeout and capture output."""
        try:
            process = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
                text=True
            )
            if process.returncode != 0:
                print(f"FFmpeg command failed (return code {process.returncode}):\n{process.stderr}")
                return None
            return process.stdout
        except subprocess.TimeoutExpired:
            print(f"FFmpeg command timed out after {timeout} seconds.")
            return None
        except FileNotFoundError:
            print("FFmpeg command not found. Please ensure FFmpeg is installed and in your PATH.")
            return None
        except Exception as e:
            print(f"Error running FFmpeg command: {e}")
            return None

    def extract_audio_from_video(self, video_path: str, output_audio_path: str) -> bool:
        """Extracts audio from a video file to a specified output path."""
        if not CV2_AVAILABLE:
            print("OpenCV not available, cannot extract audio.")
            return False
        
        command = [
            'ffmpeg', '-i', video_path, '-vn', '-acodec', 'pcm_s16le', 
            '-ar', '16000', '-ac', '1', output_audio_path
        ]
        print(f"DEBUG: Running FFmpeg audio extraction: {' '.join(command)}")
        return self._run_ffmpeg_command(command, timeout=600) is not None # Increased timeout for audio extraction

    async def transcribe_audio_file(self, audio_path: str) -> str:
        """Transcribes an audio file using Whisper."""
        if not WHISPER_AVAILABLE:
            return "Whisper not available for transcription."
        if not Path(audio_path).exists() or os.path.getsize(audio_path) == 0:
            return "Audio file not found or is empty for transcription."
        
        try:
            if self.whisper_model is None:
                print("DEBUG: Loading Whisper model for the first time...")
                self.whisper_model = whisper.load_model("base")
                print("DEBUG: Whisper model loaded.")
            
            result = self.whisper_model.transcribe(
                audio_path, 
                language=None, 
                task="transcribe",
                verbose=False,
                word_timestamps=True
            )
            
            if "segments" in result:
                transcription_parts = []
                for segment in result["segments"]:
                    start_time = segment.get("start", 0)
                    text = segment["text"].strip()
                    if text:
                        minutes = int(start_time // 60)
                        seconds = int(start_time % 60)
                        timestamp = f"[{minutes:02d}:{seconds:02d}]"
                        transcription_parts.append(f"{timestamp} {text}")
                return "\n".join(transcription_parts)
            else:
                return result["text"].strip()
        except Exception as e:
            print(f"Error during audio transcription of {audio_path}: {e}")
            return f"Audio transcription failed: {str(e)}"

    def _image_to_base64(self, image_input: PILImage.Image, max_size_kb: int = 1024) -> Optional[str]:
        """Converts an image (PIL Image) to a base64 string, resizing if necessary."""
        if not PILImage: # Use PILImage here
            return None
        
        img = image_input

        try:
            if img.mode != 'RGB':
                img = img.convert('RGB')

            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG')
            
            if img_byte_arr.tell() > max_size_kb * 1024:
                quality = 90
                while img_byte_arr.tell() > max_size_kb * 1024 and quality >= 30:
                    width, height = img.size
                    scale_factor = 0.7 if img_byte_arr.tell() > max_size_kb * 1024 * 2 else 0.9
                    new_size = (int(width * scale_factor), int(height * scale_factor))
                    img = img.resize(new_size, PILImage.Resampling.LANCZOS) # Use PILImage.Resampling
                    
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format='JPEG', quality=quality)
                    quality -= 10

            return base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
        except Exception as e:
            print(f"Error converting image to base64: {e}")
            return None

    def _extract_text_from_image_frame(self, image_frame: np.ndarray) -> str:
        """Extract text from a single image frame using OCR with preprocessing."""
        if not OCR_AVAILABLE or not PILImage: # Use PILImage here
            return "OCR not available."
        
        try:
            img_pil = PILImage.fromarray(cv2.cvtColor(image_frame, cv2.COLOR_BGR2RGB))
            
            if img_pil.mode != 'RGB':
                img_pil = img_pil.convert('RGB')
            
            width, height = img_pil.size
            if width < 300 or height < 300:
                scale_factor = max(300/width, 300/height)
                new_size = (int(width * scale_factor), int(height * scale_factor))
                img_pil = img_pil.resize(new_size, PILImage.Resampling.LANCZOS) # Use PILImage.Resampling
            elif width > 3000 or height > 3000:
                scale_factor = min(3000/width, 3000/height)
                new_size = (int(width * scale_factor), int(height * scale_factor))
                img_pil = img_pil.resize(new_size, PILImage.Resampling.LANCZOS) # Use PILImage.Resampling
            
            img_pil = img_pil.convert('L') # Grayscale
            
            # Apply preprocessing (MedianFilter, Contrast, Sharpness, Autocontrast)
            from PIL import ImageEnhance, ImageFilter, ImageOps
            img_pil = img_pil.filter(ImageFilter.MedianFilter(size=3))
            enhancer = ImageEnhance.Contrast(img_pil)
            img_pil = enhancer.enhance(1.5)
            enhancer = ImageEnhance.Sharpness(img_pil)
            img_pil = enhancer.enhance(1.2)
            img_pil = ImageOps.autocontrast(img_pil)
            
            configs = [
                r'--oem 3 --psm 6',
                r'--oem 3 --psm 3',
            ]
            
            best_text = ""
            for config in configs:
                try:
                    extracted_text = pytesseract.image_to_string(img_pil, config=config)
                    if len(extracted_text.strip()) > len(best_text.strip()):
                        best_text = extracted_text
                except Exception:
                    continue
            
            if best_text:
                lines = [line.strip() for line in best_text.split('\n') if line.strip()]
                cleaned_text = '\n'.join(lines)
                if len(cleaned_text.strip()) < 3:
                    return "Image contains minimal or no readable text"
                return cleaned_text
            else:
                return "No text detected in image"
                
        except Exception as e:
            print(f"OCR extraction failed for image frame: {e}")
            return f"OCR failed: {str(e)}"

    async def process_video(self, video_path: str, num_keyframes: int = 3, max_frame_size_kb: int = 512) -> Dict[str, Any]:
        """Processes a video file to extract audio transcription, OCR text from frames, and base64 keyframes."""
        if not CV2_AVAILABLE:
            return {"content": "Video processing dependencies not available.", "base64_video_frames": []}

        video_content_text = []
        keyframes_base64 = []
        audio_transcription = ""

        try:
            # 1. Extract Audio and Transcribe
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio_file:
                audio_path = temp_audio_file.name
            
            if self.extract_audio_from_video(video_path, audio_path):
                audio_transcription = await self.transcribe_audio_file(audio_path)
                os.unlink(audio_path)
            else:
                audio_transcription = "Audio extraction failed."

            # 2. Extract Keyframes and perform OCR
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                print(f"Error: Could not open video file {video_path}")
                return {"content": "Could not open video file.", "base64_video_frames": []}

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            if total_frames == 0 or fps == 0:
                cap.release()
                return {"content": "Video has no frames or invalid FPS.", "base64_video_frames": []}

            frame_indices = np.linspace(0, total_frames - 1, num_keyframes, dtype=int)
            
            for i, frame_idx in enumerate(frame_indices):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if not ret:
                    continue

                # Perform OCR on frame
                frame_text = self._extract_text_from_image_frame(frame)
                if frame_text and len(frame_text.strip()) > 10 and not frame_text.startswith(("OCR", "No text", "Image")):
                    timestamp = frame_idx / fps
                    minutes = int(timestamp // 60)
                    seconds = int(timestamp % 60)
                    video_content_text.append(f"[{minutes:02d}:{seconds:02d}] {frame_text.strip()}")

                # Convert frame to base64
                base64_str = self._image_to_base64(PILImage.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)), max_size_kb=max_frame_size_kb)
                if base64_str:
                    keyframes_base64.append(base64_str)
            
            cap.release()

            combined_content = []
            if audio_transcription and len(audio_transcription.strip()) > 20:
                combined_content.append(f"=== AUDIO TRANSCRIPTION ===\n{audio_transcription}")
            if video_content_text:
                combined_content.append(f"\n=== TEXT FROM VIDEO FRAMES ===\n" + "\n".join(video_content_text))
            
            return {
                "content": "\n\n".join(combined_content),
                "base64_video_frames": keyframes_base64
            }

        except Exception as e:
            print(f"Error processing video {video_path}: {e}")
            return {"content": f"Video processing failed: {str(e)}", "base64_video_frames": []}
