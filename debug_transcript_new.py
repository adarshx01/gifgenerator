from youtube_transcript_api import YouTubeTranscriptApi
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_transcript_new_api(video_id):
    """Debug transcript access using the new API"""
    try:
        logger.info(f"Debugging transcript access for video: {video_id}")
        
        # Initialize the API
        ytt_api = YouTubeTranscriptApi()
        
        # List available transcripts
        transcript_list = ytt_api.list(video_id)
        logger.info("Available transcripts:")
        
        available_transcripts = []
        for transcript in transcript_list:
            logger.info(f"  - {transcript.language_code}: {transcript.language} (Generated: {transcript.is_generated}, Translatable: {transcript.is_translatable})")
            available_transcripts.append(transcript)
        
        # Try to fetch each transcript
        for transcript in available_transcripts:
            try:
                logger.info(f"\nTrying to fetch transcript: {transcript.language_code}")
                fetched_transcript = transcript.fetch()
                logger.info(f"SUCCESS: Fetched {len(fetched_transcript)} entries")
                
                # Convert to raw data for compatibility
                raw_data = fetched_transcript.to_raw_data()
                logger.info("First 3 entries:")
                for i, entry in enumerate(raw_data[:3]):
                    logger.info(f"  {i+1}: {entry}")
                    
                # If this is the first successful one, return it
                return raw_data, transcript.language_code
                
            except Exception as e:
                logger.error(f"FAILED to fetch {transcript.language_code}: {e}")
                continue
        
        logger.error("No transcripts could be fetched")
        return None, None
        
    except Exception as e:
        logger.error(f"Error listing transcripts: {e}")
        return None, None

def test_translation(video_id):
    """Test translation functionality"""
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.list(video_id)
        
        # Find Hindi transcript and try to translate
        for transcript in transcript_list:
            if transcript.language_code == 'hi' and transcript.is_translatable:
                try:
                    logger.info(f"Attempting to translate {transcript.language_code} to English")
                    translated_transcript = transcript.translate('en')
                    fetched_translated = translated_transcript.fetch()
                    raw_data = fetched_translated.to_raw_data()
                    
                    logger.info(f"SUCCESS: Translated transcript has {len(raw_data)} entries")
                    logger.info("First 3 translated entries:")
                    for i, entry in enumerate(raw_data[:3]):
                        logger.info(f"  {i+1}: {entry}")
                    
                    return raw_data, 'en'
                except Exception as translate_error:
                    logger.error(f"Translation failed: {translate_error}")
                    break
        
        return None, None
        
    except Exception as e:
        logger.error(f"Translation test failed: {e}")
        return None, None

if __name__ == "__main__":
    video_id = "a3VLxRfWBbA"
    
    print("=== Testing direct transcript fetch ===")
    transcript, lang_code = debug_transcript_new_api(video_id)
    
    if transcript:
        print(f"\n✅ Successfully got transcript in {lang_code}")
        print(f"Total entries: {len(transcript)}")
    else:
        print("\n❌ Could not get any transcript")
    
    print("\n=== Testing translation ===")
    translated_transcript, translated_lang = test_translation(video_id)
    
    if translated_transcript:
        print(f"\n✅ Successfully got translated transcript in {translated_lang}")
        print(f"Total entries: {len(translated_transcript)}")
    else:
        print("\n❌ Could not get translated transcript")