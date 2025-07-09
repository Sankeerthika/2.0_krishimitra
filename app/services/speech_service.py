"""
Simple Speech-to-Text Service

Supports multiple audio formats with automatic conversion:
- OGG (WhatsApp format) - directly supported by Google Cloud Speech
- WAV, FLAC, MP3 - supported formats
- Automatic conversion using ffmpeg as fallback

Requirements:
- google-cloud-speech (for best quality)
- SpeechRecognition (for free tier fallback)
- ffmpeg (for audio conversion)

Install ffmpeg: https://ffmpeg.org/download.html
"""

import logging
import os
import tempfile
from dotenv import load_dotenv
import requests
import json
import subprocess

load_dotenv()

def check_ffmpeg_installed():
    """Check if ffmpeg is available"""
    try:
        # First try the standard PATH
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            return True
    except FileNotFoundError:
        pass
    
    # Try the WinGet installation path
    try:
        username = os.environ.get('USERNAME', '')
        winget_ffmpeg = f"C:\\Users\\{username}\\AppData\\Local\\Microsoft\\WinGet\\Packages\\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\\ffmpeg-7.1.1-full_build\\bin\\ffmpeg.exe"
        if os.path.exists(winget_ffmpeg):
            result = subprocess.run([winget_ffmpeg, '-version'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
    except Exception:
        pass
    
    return False

def convert_ogg_to_wav_pydub(ogg_path):
    """Convert OGG file to WAV using pydub (alternative to ffmpeg)"""
    try:
        from pydub import AudioSegment
        from pydub.utils import which
        import os
        
        # Set ffmpeg path explicitly for pydub
        # First try to find ffmpeg in PATH
        ffmpeg_path = which("ffmpeg")
        
        # If not found, try the WinGet installation path
        if not ffmpeg_path:
            username = os.environ.get('USERNAME', '')
            winget_ffmpeg = f"C:\\Users\\{username}\\AppData\\Local\\Microsoft\\WinGet\\Packages\\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\\ffmpeg-7.1.1-full_build\\bin\\ffmpeg.exe"
            if os.path.exists(winget_ffmpeg):
                ffmpeg_path = winget_ffmpeg
                
        if ffmpeg_path:
            AudioSegment.converter = ffmpeg_path
            AudioSegment.ffmpeg = ffmpeg_path
            # Also try to find ffprobe
            ffprobe_path = which("ffprobe")
            if not ffprobe_path and ffmpeg_path:
                ffprobe_path = ffmpeg_path.replace("ffmpeg.exe", "ffprobe.exe")
                if os.path.exists(ffprobe_path):
                    AudioSegment.ffprobe = ffprobe_path
            
            logging.info(f"Using ffmpeg at: {ffmpeg_path}")
        else:
            logging.warning("FFmpeg not found, pydub may not work properly")
        
        # Load OGG file
        audio = AudioSegment.from_ogg(ogg_path)
        
        # Convert to WAV with specific settings
        audio = audio.set_frame_rate(16000)  # 16kHz sample rate
        audio = audio.set_channels(1)        # Mono
        audio = audio.set_sample_width(2)    # 16-bit
        
        # Create WAV file path
        wav_path = ogg_path.replace('.ogg', '.wav')
        
        # Export as WAV
        audio.export(wav_path, format="wav")
        
        if os.path.exists(wav_path):
            logging.info(f"Successfully converted {ogg_path} to {wav_path} using pydub")
            return wav_path
        else:
            logging.error("pydub conversion failed - no output file")
            return None
            
    except ImportError:
        logging.error("pydub library not available")
        return None
    except Exception as e:
        logging.error(f"Error converting OGG to WAV with pydub: {e}")
        return None

def convert_ogg_to_wav(ogg_path):
    """Convert OGG file to WAV using available tools"""
    # Try pydub first (simpler, no external dependencies)
    result = convert_ogg_to_wav_pydub(ogg_path)
    if result:
        return result
    
    # Fallback to ffmpeg if available
    try:
        # Check if ffmpeg is available
        if not check_ffmpeg_installed():
            logging.error("Neither pydub nor ffmpeg available for conversion")
            return None
        
        # Create temp WAV file
        wav_path = ogg_path.replace('.ogg', '.wav')
        
        # Determine ffmpeg path
        ffmpeg_cmd = 'ffmpeg'
        try:
            # Try standard PATH first
            subprocess.run([ffmpeg_cmd, '-version'], capture_output=True, text=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Try WinGet installation path
            username = os.environ.get('USERNAME', '')
            winget_ffmpeg = f"C:\\Users\\{username}\\AppData\\Local\\Microsoft\\WinGet\\Packages\\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\\ffmpeg-7.1.1-full_build\\bin\\ffmpeg.exe"
            if os.path.exists(winget_ffmpeg):
                ffmpeg_cmd = winget_ffmpeg
        
        # Use ffmpeg to convert OGG to WAV
        cmd = [
            ffmpeg_cmd, '-i', ogg_path, 
            '-acodec', 'pcm_s16le',  # Linear PCM 16-bit
            '-ar', '16000',          # Sample rate 16kHz  
            '-ac', '1',              # Mono channel
            '-y',                    # Overwrite output file
            wav_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and os.path.exists(wav_path):
            logging.info(f"Successfully converted {ogg_path} to {wav_path} using ffmpeg")
            return wav_path
        else:
            logging.error(f"FFmpeg conversion failed: {result.stderr}")
            return None
            
    except Exception as e:
        logging.error(f"Error converting OGG to WAV: {e}")
        return None

def get_audio_format(file_path):
    """Detect audio file format"""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.ogg':
        return 'ogg'
    elif ext == '.wav':
        return 'wav'
    elif ext == '.mp3':
        return 'mp3'
    elif ext == '.flac':
        return 'flac'
    else:
        return 'unknown'

def transcribe_with_google_cloud_speech(audio_path):
    """Transcribe audio using Google Cloud Speech-to-Text API"""
    try:
        from google.cloud import speech
        
        # Initialize the client
        client = speech.SpeechClient()
        
        # Read the audio file
        with open(audio_path, 'rb') as audio_file:
            content = audio_file.read()
        
        # Configure the audio
        audio = speech.RecognitionAudio(content=content)
        
        # Detect file format and configure accordingly
        file_format = get_audio_format(audio_path)
        
        if file_format == 'ogg':
            # WhatsApp OGG format
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
                sample_rate_hertz=16000,  # WhatsApp standard
                language_code="en-US",
                alternative_language_codes=["hi-IN", "es-ES", "fr-FR", "de-DE"],
                enable_automatic_punctuation=True,
                model="latest_long",
            )
        elif file_format == 'wav':
            # WAV format - let Google detect encoding automatically
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code="en-US",
                alternative_language_codes=["hi-IN", "es-ES", "fr-FR", "de-DE"],
                enable_automatic_punctuation=True,
                model="latest_long",
            )
        elif file_format == 'flac':
            # FLAC format - best quality
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.FLAC,
                language_code="en-US",
                alternative_language_codes=["hi-IN", "es-ES", "fr-FR", "de-DE"],
                enable_automatic_punctuation=True,
                model="latest_long",
            )
        else:
            # Default to LINEAR16
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code="en-US",
                enable_automatic_punctuation=True,
                model="latest_long",
            )
        
        # Perform the transcription
        response = client.recognize(config=config, audio=audio)
        
        # Extract the transcription
        transcriptions = []
        for result in response.results:
            transcriptions.append(result.alternatives[0].transcript)
        
        if transcriptions:
            transcribed_text = " ".join(transcriptions).strip()
            logging.info(f"Google Cloud Speech transcription: {transcribed_text}")
            return transcribed_text
        else:
            logging.warning("Google Cloud Speech returned no results")
            return None
            
    except ImportError:
        logging.error("google-cloud-speech library not installed")
        return None
    except Exception as e:
        logging.error(f"Google Cloud Speech error: {str(e)}")
        return None


def transcribe_with_google_web_speech(audio_path):
    """Transcribe using Google Web Speech API (free tier) with file conversion"""
    try:
        import speech_recognition as sr
        
        # Initialize recognizer
        recognizer = sr.Recognizer()
        
        # Convert OGG to WAV if needed (speech_recognition doesn't handle OGG well)
        working_path = audio_path
        converted_file = None
        
        if get_audio_format(audio_path) == 'ogg':
            logging.info("Converting OGG to WAV for speech_recognition library")
            converted_file = convert_ogg_to_wav(audio_path)
            if converted_file:
                working_path = converted_file
            else:
                logging.error("Failed to convert OGG file")
                return None
        
        # Try to read the audio file
        try:
            with sr.AudioFile(working_path) as source:
                # Adjust for ambient noise and record
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio_data = recognizer.record(source)
            
            # Use Google's free speech recognition
            transcribed_text = recognizer.recognize_google(
                audio_data, 
                language="en-US",
                show_all=False
            )
            
            # Clean up converted file if it exists
            if converted_file and os.path.exists(converted_file):
                try:
                    os.remove(converted_file)
                except:
                    pass
            
            if transcribed_text:
                logging.info(f"Google Web Speech transcription: {transcribed_text}")
                return transcribed_text.strip()
            else:
                return None
                
        except sr.UnknownValueError:
            logging.warning("Google Web Speech could not understand the audio")
            return None
        except sr.RequestError as e:
            logging.error(f"Google Web Speech API error: {e}")
            return None
        finally:
            # Clean up converted file if it exists
            if converted_file and os.path.exists(converted_file):
                try:
                    os.remove(converted_file)
                except:
                    pass
            
    except Exception as e:
        logging.error(f"Google Web Speech error: {str(e)}")
        return None


def setup_google_cloud_auth():
    """Setup Google Cloud authentication using the same project as Gemini"""
    try:
        # Check if we can use the same Google credentials
        import google.auth
        from google.auth.exceptions import DefaultCredentialsError
        
        try:
            credentials, project = google.auth.default()
            if project:
                logging.info(f"Using Google Cloud project: {project}")
                return True
            else:
                logging.info("Google credentials available but no project set")
                return False
        except DefaultCredentialsError:
            logging.info("No default Google credentials found")
            return False
            
    except ImportError:
        logging.error("google-auth library not available")
        return False


def transcribe_audio(audio_path, preferred_service="web_speech"):
    """Main function to transcribe audio with proper format handling"""
    if not os.path.exists(audio_path):
        logging.error(f"Audio file not found: {audio_path}")
        return None
    
    # Check file size
    file_size = os.path.getsize(audio_path)
    if file_size > 10 * 1024 * 1024:  # 10MB limit
        logging.error(f"Audio file too large: {file_size} bytes")
        return "Voice message too large. Please send a shorter recording."
    
    if file_size == 0:
        logging.error("Audio file is empty")
        return None
    
    # Detect file format
    file_format = get_audio_format(audio_path)
    logging.info(f"Transcribing {file_format} audio: {audio_path} ({file_size} bytes)")
    
    # Skip Google Cloud Speech (credentials issue) and go directly to free tier
    if preferred_service == "google_cloud":
        logging.info("Skipping Google Cloud Speech (credentials not configured), using free tier")
        preferred_service = "web_speech"
    
    # Use Google Web Speech (with conversion if needed)
    result = transcribe_with_google_web_speech(audio_path)
    if result:
        return result
    
    # If free tier fails, provide helpful message
    logging.error("Google Web Speech service failed")
    return "I received your voice message! 🎤 However, I'm having trouble with speech recognition right now. Could you please send your message as text? I'd be happy to help!"
