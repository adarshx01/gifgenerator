from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from google import genai
from google.genai import types
import http.client
import json
import re
import os
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from moviepy.config import change_settings
import requests
from dotenv import load_dotenv
import uuid
import logging
import yt_dlp
import subprocess

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure ImageMagick for MoviePy
def setup_imagemagick():
    """Setup ImageMagick for text rendering"""
    try:
        # Try to find ImageMagick binary
        imagemagick_paths = [
            '/usr/bin/convert',  # Ubuntu/Debian
            '/usr/local/bin/convert',  # macOS with Homebrew
            '/opt/homebrew/bin/convert',  # macOS with Apple Silicon
            'convert'  # Windows or if in PATH
        ]
        
        imagemagick_binary = None
        for path in imagemagick_paths:
            try:
                result = subprocess.run([path, '-version'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0 and 'ImageMagick' in result.stdout:
                    imagemagick_binary = path
                    logger.info(f"Found ImageMagick at: {path}")
                    break
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                continue
        
        if imagemagick_binary:
            change_settings({"IMAGEMAGICK_BINARY": imagemagick_binary})
            logger.info("ImageMagick configured successfully")
            return True
        else:
            logger.warning("ImageMagick not found - text overlay will be disabled")
            return False
    except Exception as e:
        logger.error(f"Error setting up ImageMagick: {e}")
        return False

# Setup ImageMagick on startup
IMAGEMAGICK_AVAILABLE = setup_imagemagick()

app = FastAPI(title="GIF Generator API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini with new API
try:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY not found in environment variables")
        raise ValueError("GEMINI_API_KEY not found")
    
    # Set the API key for the client
    os.environ["GEMINI_API_KEY"] = api_key
    client = genai.Client(api_key="AIzaSyAFWpODYF9_BAwFuEIKUE6_9OyRfN-w150")
    logger.info("Gemini configured successfully with new API")
except Exception as e:
    logger.error(f"Failed to configure Gemini: {e}")
    client = None

# RapidAPI Configuration
RAPIDAPI_KEY = "faac326673msh3ca31bdf3e8902bp19f308jsn73fc2f66712a"
RAPIDAPI_HOST = "youtube-transcriptor.p.rapidapi.com"

# Create uploads directory
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("output")
YOUTUBE_DIR = Path("youtube_downloads")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
YOUTUBE_DIR.mkdir(exist_ok=True)

class GIFProcessor:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def extract_youtube_id(self, url: str) -> str:
        """Extract YouTube video ID from URL"""
        logger.info(f"Extracting YouTube ID from URL: {url}")
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
            r'youtube\.com\/watch\?.*v=([^&\n?#]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                video_id = match.group(1)
                logger.info(f"Extracted video ID: {video_id}")
                return video_id
        raise ValueError(f"Invalid YouTube URL: {url}")
    
    def download_youtube_video(self, video_id: str) -> str:
        """Download YouTube video and return local file path"""
        try:
            logger.info(f"Downloading YouTube video: {video_id}")
            
            # Check if already downloaded
            existing_files = list(YOUTUBE_DIR.glob(f"{video_id}.*"))
            if existing_files:
                logger.info(f"Video already downloaded: {existing_files[0]}")
                return str(existing_files[0])
            
            # Configure yt-dlp options
            ydl_opts = {
                'format': 'best[height<=480]/best',  # Lower quality for faster processing
                'outtmpl': str(YOUTUBE_DIR / f'{video_id}.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
            }
            
            url = f"https://www.youtube.com/watch?v={video_id}"
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Download the video
                ydl.download([url])
                
                # Find the downloaded file
                downloaded_files = list(YOUTUBE_DIR.glob(f"{video_id}.*"))
                if downloaded_files:
                    logger.info(f"Successfully downloaded: {downloaded_files[0]}")
                    return str(downloaded_files[0])
                else:
                    raise Exception("Download completed but file not found")
                    
        except Exception as e:
            logger.error(f"Failed to download YouTube video {video_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to download YouTube video. This might be due to:\n"
                       f"• Video is private or restricted\n"
                       f"• Copyright restrictions\n"
                       f"• Network issues\n"
                       f"Error: {str(e)}"
            )
    
    def get_available_languages(self, video_id: str) -> List[Dict]:
        """Get list of available transcript languages using RapidAPI"""
        try:
            logger.info(f"Getting available languages for video: {video_id}")
            
            conn = http.client.HTTPSConnection(RAPIDAPI_HOST)
            headers = {
                'x-rapidapi-key': RAPIDAPI_KEY,
                'x-rapidapi-host': RAPIDAPI_HOST
            }
            
            # Make request to get video info (which includes available languages)
            logger.info(f"Making request to: https://{RAPIDAPI_HOST}/transcript?video_id={video_id}&lang=en")
            conn.request("GET", f"/transcript?video_id={video_id}&lang=en", headers=headers)
            res = conn.getresponse()
            data = res.read()
            
            logger.info(f"Response status: {res.status}")
            logger.info(f"Response reason: {res.reason}")
            logger.info(f"Response data length: {len(data) if data else 0}")
            
            if res.status != 200:
                error_message = f"RapidAPI request failed with status {res.status}: {res.reason}"
                if data:
                    try:
                        error_data = data.decode("utf-8")
                        logger.error(f"Error response body: {error_data}")
                        error_message += f". Response: {error_data}"
                    except:
                        logger.error(f"Could not decode error response")
                raise HTTPException(status_code=res.status, detail=error_message)
            
            if not data:
                raise HTTPException(status_code=500, detail="Empty response from transcript service")
            
            try:
                response_data = json.loads(data.decode("utf-8"))
                logger.info(f"Parsed response data type: {type(response_data)}")
                logger.info(f"Response data: {response_data}")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Raw response: {data.decode('utf-8', errors='ignore')}")
                raise HTTPException(status_code=500, detail="Invalid JSON response from transcript service")
            
            if not response_data or len(response_data) == 0:
                raise HTTPException(status_code=404, detail="No transcript data found for this video")
            
            # Extract available languages from the response
            video_info = response_data[0] if isinstance(response_data, list) else response_data
            available_langs = video_info.get('availableLangs', [])
            
            logger.info(f"Available languages from API: {available_langs}")
            
            if not available_langs:
                # If no availableLangs field, try to infer from the current response
                logger.warning("No availableLangs field found, creating default language list")
                available_langs = ['en']  # Default to English
            
            # Convert to our format
            languages = []
            for lang_code in available_langs:
                # Map common language codes to readable names
                lang_names = {
                    'en': 'English',
                    'hi': 'Hindi',
                    'es': 'Spanish',
                    'fr': 'French',
                    'de': 'German',
                    'zh-CN': 'Chinese (Simplified)',
                    'zh-Hant': 'Chinese (Traditional)',
                    'ja': 'Japanese',
                    'ko': 'Korean',
                    'pt': 'Portuguese',
                    'ru': 'Russian',
                    'ar': 'Arabic',
                    'it': 'Italian',
                    'tr': 'Turkish',
                    'th': 'Thai',
                    'vi': 'Vietnamese',
                    'id': 'Indonesian',
                    'ta': 'Tamil',
                    'pa': 'Punjabi',
                    'pl': 'Polish',
                    'es-ES': 'Spanish (Spain)'
                }
                
                languages.append({
                    'language_code': lang_code,
                    'language_name': lang_names.get(lang_code, lang_code.upper()),
                    'is_generated': True,  # RapidAPI transcripts are typically auto-generated
                    'is_translatable': True
                })
            
            logger.info(f"Found {len(languages)} available languages")
            return languages
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting available languages: {e}")
            logger.error(f"Error type: {type(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Could not access transcript information for video {video_id}. Error: {str(e)}"
            )
    
    def get_transcript_by_language(self, video_id: str, language_code: str) -> List[Dict]:
        """Get transcript in specific language using RapidAPI"""
        try:
            logger.info(f"Getting transcript for video {video_id} in language {language_code}")
            
            conn = http.client.HTTPSConnection(RAPIDAPI_HOST)
            headers = {
                'x-rapidapi-key': RAPIDAPI_KEY,
                'x-rapidapi-host': RAPIDAPI_HOST
            }
            
            # Make request to get transcript
            logger.info(f"Making request to: https://{RAPIDAPI_HOST}/transcript?video_id={video_id}&lang={language_code}")
            conn.request("GET", f"/transcript?video_id={video_id}&lang={language_code}", headers=headers)
            res = conn.getresponse()
            data = res.read()
            
            logger.info(f"Response status: {res.status}")
            logger.info(f"Response reason: {res.reason}")
            
            if res.status != 200:
                error_message = f"RapidAPI request failed with status {res.status}: {res.reason}"
                if data:
                    try:
                        error_data = data.decode("utf-8")
                        logger.error(f"Error response body: {error_data}")
                        error_message += f". Response: {error_data}"
                    except:
                        pass
                raise HTTPException(status_code=res.status, detail=error_message)
            
            response_data = json.loads(data.decode("utf-8"))
            
            if not response_data or len(response_data) == 0:
                raise HTTPException(status_code=404, detail=f"No transcript found for video {video_id} in language {language_code}")
            
            # Extract transcription data
            video_info = response_data[0] if isinstance(response_data, list) else response_data
            transcription = video_info.get('transcription', [])
            
            if not transcription:
                raise HTTPException(status_code=404, detail=f"No transcription data available for this video in {language_code}")
            
            # Convert to standard format (compatible with youtube-transcript-api format)
            formatted_transcript = []
            for item in transcription:
                formatted_transcript.append({
                    'text': item.get('subtitle', ''),
                    'start': item.get('start', 0),
                    'duration': item.get('dur', 3)
                })
            
            logger.info(f"Successfully retrieved transcript with {len(formatted_transcript)} entries")
            return formatted_transcript
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise HTTPException(status_code=500, detail="Invalid response from transcript service")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting transcript: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Error accessing transcript for video {video_id}: {str(e)}"
            )
    
    def translate_text_with_gemini(self, text: str, target_language: str = "English") -> str:
        """Use Gemini to translate text with new API"""
        if not client:
            logger.warning("Gemini not available for translation")
            return text
        
        try:
            prompt = f"Translate this text to {target_language}. Only return the translated text, nothing else: {text}"
            
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            
            translated = response.text.strip()
            logger.info(f"Translated text: {translated[:100]}...")
            return translated
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return text
    
    def analyze_with_gemini(self, transcript: List[Dict], prompt: str, original_language: str = "English") -> List[Dict]:
        """Use Gemini to analyze transcript and find key moments with new API"""
        if not client:
            logger.warning("Gemini not configured, using fallback analysis")
            return self.fallback_analysis(transcript, prompt)
        
        # Combine transcript into readable text
        full_text = " ".join([item['text'] for item in transcript])
        logger.info(f"Analyzing transcript with {len(full_text)} characters")
        
        # Limit text to avoid token limits
        if len(full_text) > 2000:
            full_text = full_text[:2000] + "..."
        
        language_note = f"Note: The transcript is in {original_language}." if original_language != "English" else ""
        
        gemini_prompt = f"""
        Analyze this video transcript and the user's theme prompt to find 2-3 key moments that would make great GIFs.
        {language_note}
        
        User's theme: {prompt}
        
        Transcript: {full_text}
        
        Please identify 2-3 specific quotes/moments that match the theme. For each moment, provide:
        1. The exact text/quote from the transcript (keep in original language)
        2. Why it fits the theme
        3. A brief description of what makes it GIF-worthy
        
        Format your response as JSON with this structure:
        {{
            "moments": [
                {{
                    "quote": "exact quote from transcript in original language",
                    "reason": "why it fits the theme",
                    "description": "what makes it GIF-worthy"
                }}
            ]
        }}
        """
        
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=gemini_prompt,
            )
            
            response_text = response.text
            logger.info(f"Gemini response: {response_text[:200]}...")
            
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    analysis = json.loads(json_match.group())
                    moments = analysis.get('moments', [])
                    logger.info(f"Gemini found {len(moments)} moments")
                    return moments
                except json.JSONDecodeError as je:
                    logger.error(f"Failed to parse Gemini JSON: {je}")
                    return self.fallback_analysis(transcript, prompt)
            else:
                logger.warning("No JSON found in Gemini response, using fallback")
                return self.fallback_analysis(transcript, prompt)
        except Exception as e:
            logger.error(f"Gemini analysis failed: {e}")
            return self.fallback_analysis(transcript, prompt)
    
    def fallback_analysis(self, transcript: List[Dict], prompt: str) -> List[Dict]:
        """Fallback analysis if Gemini fails"""
        logger.info("Using fallback analysis")
        keywords = prompt.lower().split()
        moments = []
        
        # Try keyword matching first
        for item in transcript[:20]:
            text_lower = item['text'].lower()
            if any(keyword in text_lower for keyword in keywords):
                moments.append({
                    "quote": item['text'],
                    "reason": f"Contains keywords related to '{prompt}'",
                    "description": "Selected based on keyword matching"
                })
                if len(moments) >= 3:
                    break
        
        # If no keyword matches, take distributed moments
        if not moments:
            transcript_length = len(transcript)
            if transcript_length > 0:
                indices = [0]
                if transcript_length > 1:
                    indices.append(transcript_length // 2)
                if transcript_length > 2:
                    indices.append(transcript_length - 1)
                
                for i, idx in enumerate(indices[:3]):
                    moments.append({
                        "quote": transcript[idx]['text'],
                        "reason": f"Sample moment from video ({['beginning', 'middle', 'end'][i]})",
                        "description": f"Selected from video {['beginning', 'middle', 'end'][i]} - matches theme: {prompt}"
                    })
        
        logger.info(f"Fallback analysis found {len(moments)} moments")
        return moments
    
    def find_timestamp_for_quote(self, transcript: List[Dict], quote: str) -> Optional[Dict]:
        """Find timestamp for a specific quote in transcript"""
        for item in transcript:
            if quote.lower() in item['text'].lower() or item['text'].lower() in quote.lower():
                return {
                    'start': item['start'],
                    'duration': item.get('duration', 3),
                    'text': item['text']
                }
        
        if transcript:
            return {
                'start': transcript[0]['start'],
                'duration': transcript[0].get('duration', 3),
                'text': transcript[0]['text']
            }
        return None
    
    def create_gif_with_caption(self, video_path: str, start_time: float, duration: float, caption: str, output_path: str) -> str:
        """Create GIF with caption overlay"""
        try:
            logger.info(f"Creating GIF from {video_path} at {start_time}s for {duration}s")
            clip = VideoFileClip(video_path).subclip(start_time, start_time + duration)
            clip = clip.resize(width=480)
            
            # Try to add text overlay if ImageMagick is available
            if IMAGEMAGICK_AVAILABLE and caption.strip():
                try:
                    # Split long captions into multiple lines
                    max_chars_per_line = 30  # Reduced for better readability
                    words = caption.split()
                    lines = []
                    current_line = ""
                    
                    for word in words:
                        if len(current_line + " " + word) <= max_chars_per_line:
                            current_line = current_line + " " + word if current_line else word
                        else:
                            if current_line:
                                lines.append(current_line)
                            current_line = word
                    
                    if current_line:
                        lines.append(current_line)
                    
                    # Join lines with newlines, limit to 3 lines
                    final_caption = "\n".join(lines[:3])
                    
                    logger.info(f"Creating text clip with caption: {final_caption}")
                    
                    # Create text clip with better settings for multi-language support
                    txt_clip = TextClip(
                        final_caption, 
                        fontsize=16,
                        color='white', 
                        stroke_color='black',
                        stroke_width=2,
                        method='caption',  # Better for multi-line text
                        size=(clip.w - 40, None),  # Limit width with padding
                        align='center'
                    )
                    
                    # Position text at bottom center with margin
                    txt_clip = txt_clip.set_position(('center', clip.h - txt_clip.h - 20)).set_duration(duration)
                    final_clip = CompositeVideoClip([clip, txt_clip])
                    
                    # Write GIF
                    final_clip.write_gif(output_path, fps=10, opt='OptimizeTransparency')
                    
                    # Clean up
                    clip.close()
                    txt_clip.close()
                    final_clip.close()
                    
                    logger.info(f"GIF with text created successfully: {output_path}")
                    return output_path
                    
                except Exception as text_error:
                    logger.warning(f"Text overlay failed: {text_error}, creating GIF without text")
                    clip.write_gif(output_path, fps=10, opt='OptimizeTransparency')
                    clip.close()
            else:
                logger.info("Creating GIF without text overlay (ImageMagick not available or no caption)")
                clip.write_gif(output_path, fps=10, opt='OptimizeTransparency')
                clip.close()
            
            logger.info(f"GIF created successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating GIF: {e}")
            raise HTTPException(status_code=500, detail=f"Error creating GIF: {str(e)}")

gif_processor = GIFProcessor()

@app.get("/")
async def root():
    imagemagick_status = "✅ Available" if IMAGEMAGICK_AVAILABLE else "❌ Not Available (text overlay disabled)"
    return {
        "message": "GIF Generator API is running with RapidAPI YouTube Transcriptor and new Gemini API!",
        "imagemagick_status": imagemagick_status
    }

@app.get("/get-languages/{video_id}")
async def get_languages(video_id: str):
    """Get available transcript languages for a YouTube video"""
    try:
        languages = gif_processor.get_available_languages(video_id)
        return {
            "success": True,
            "languages": languages,
            "message": f"Found {len(languages)} available languages"
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error getting languages: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/process-youtube")
async def process_youtube(
    url: str = Form(...),
    prompt: str = Form(...),
    language_code: str = Form(...)
):
    """Process YouTube video with selected language"""
    logger.info(f"Processing YouTube URL: {url} with prompt: {prompt} in language: {language_code}")
    
    try:
        video_id = gif_processor.extract_youtube_id(url)
        transcript = gif_processor.get_transcript_by_language(video_id, language_code)
        
        # Get language info for analysis
        try:
            languages = gif_processor.get_available_languages(video_id)
            selected_language = next((lang for lang in languages if lang['language_code'] == language_code), None)
            language_name = selected_language['language_name'] if selected_language else language_code
        except:
            language_name = language_code
        
        moments = gif_processor.analyze_with_gemini(transcript, prompt, language_name)
        
        gif_suggestions = []
        for moment in moments:
            timestamp_data = gif_processor.find_timestamp_for_quote(transcript, moment['quote'])
            if timestamp_data:
                gif_suggestions.append({
                    **moment,
                    'start_time': timestamp_data['start'],
                    'duration': min(timestamp_data['duration'], 5),
                    'video_id': video_id,
                    'language_code': language_code,
                    'language_name': language_name
                })
        
        logger.info(f"Successfully processed YouTube video, found {len(gif_suggestions)} suggestions")
        return {
            "success": True,
            "video_id": video_id,
            "language_code": language_code,
            "language_name": language_name,
            "gif_suggestions": gif_suggestions,
            "message": f"Found {len(gif_suggestions)} potential GIF moments in {language_name}",
            "text_overlay_available": IMAGEMAGICK_AVAILABLE
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/process-upload")
async def process_upload(
    file: UploadFile = File(...),
    prompt: str = Form(...)
):
    """Process uploaded video and generate GIF suggestions"""
    logger.info(f"Processing uploaded file: {file.filename} with prompt: {prompt}")
    
    try:
        file_id = str(uuid.uuid4())
        file_path = UPLOAD_DIR / f"{file_id}_{file.filename}"
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"File saved to: {file_path}")
        
        try:
            clip = VideoFileClip(str(file_path))
            duration = clip.duration
            clip.close()
            
            logger.info(f"Video duration: {duration} seconds")
            
            moments = []
            num_moments = min(3, max(1, int(duration // 10)))
            
            for i in range(num_moments):
                start_time = i * (duration / num_moments)
                moment_duration = min(5, duration - start_time, duration / num_moments)
                moments.append({
                    "quote": f"Moment {i+1} from uploaded video - {prompt}",
                    "reason": f"Matches theme: {prompt}",
                    "description": f"Sample moment at {start_time:.1f}s",
                    "start_time": start_time,
                    "duration": moment_duration,
                    "file_id": file_id
                })
            
            logger.info(f"Created {len(moments)} moments for uploaded video")
            return {
                "success": True,
                "file_id": file_id,
                "gif_suggestions": moments,
                "message": f"Analyzed uploaded video, found {len(moments)} potential moments",
                "text_overlay_available": IMAGEMAGICK_AVAILABLE
            }
            
        except Exception as e:
            logger.error(f"Error processing video file: {e}")
            raise HTTPException(status_code=400, detail=f"Error processing video: {str(e)}")
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error processing upload: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing upload: {str(e)}")

@app.post("/generate-gif")
async def generate_gif(
    file_id: str = Form(None),
    video_id: str = Form(None),
    start_time: float = Form(...),
    duration: float = Form(...),
    caption: str = Form(...),
    translate_to_english: bool = Form(False)
):
    """Generate GIF from video segment with optional translation"""
    logger.info(f"Generating GIF - file_id: {file_id}, video_id: {video_id}, translate: {translate_to_english}")
    
    try:
        if file_id:
            video_files = list(UPLOAD_DIR.glob(f"{file_id}_*"))
            if not video_files:
                raise HTTPException(status_code=404, detail="Uploaded file not found")
            video_path = str(video_files[0])
            logger.info(f"Using uploaded file: {video_path}")
        elif video_id:
            # Download YouTube video
            try:
                video_path = gif_processor.download_youtube_video(video_id)
                logger.info(f"Using downloaded YouTube video: {video_path}")
            except Exception as e:
                logger.error(f"Failed to download YouTube video: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to download YouTube video: {str(e)}\n\n"
                           f"Alternative: Download the video manually and upload it using the 'Upload Video' option."
                )
        else:
            raise HTTPException(status_code=400, detail="Either file_id or video_id required")
        
        # Translate caption if requested
        final_caption = caption
        if translate_to_english and caption:
            final_caption = gif_processor.translate_text_with_gemini(caption, "English")
            logger.info(f"Translated caption: {final_caption}")
        
        gif_id = str(uuid.uuid4())
        gif_path = OUTPUT_DIR / f"{gif_id}.gif"
        
        gif_processor.create_gif_with_caption(
            video_path=video_path,
            start_time=start_time,
            duration=duration,
            caption=final_caption,
            output_path=str(gif_path)
        )
        
        return {
            "success": True,
            "gif_id": gif_id,
            "original_caption": caption,
            "final_caption": final_caption,
            "translated": translate_to_english,
            "text_overlay_available": IMAGEMAGICK_AVAILABLE,
            "message": "GIF generated successfully" + ("" if IMAGEMAGICK_AVAILABLE else " (without text overlay)")
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error generating GIF: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating GIF: {str(e)}")

@app.get("/download-gif/{gif_id}")
async def download_gif(gif_id: str):
    """Download generated GIF"""
    gif_path = OUTPUT_DIR / f"{gif_id}.gif"
    
    if not gif_path.exists():
        raise HTTPException(status_code=404, detail="GIF not found")
    
    return FileResponse(
        path=str(gif_path),
        media_type="image/gif",
        filename=f"generated_{gif_id}.gif"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
