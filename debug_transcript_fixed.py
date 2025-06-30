from youtube_transcript_api import YouTubeTranscriptApi
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_transcript_correct_api(video_id):
    """Debug transcript access using the correct API"""
    try:
        logger.info(f"Debugging transcript access for video: {video_id}")
        
        # Try to get transcript directly first
        try:
            logger.info("Trying to get English transcript directly...")
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
            logger.info(f"SUCCESS: Got English transcript with {len(transcript)} entries")
            return transcript, 'en'
        except Exception as en_error:
            logger.warning(f"English transcript failed: {en_error}")
        
        # Try to get Hindi transcript
        try:
            logger.info("Trying to get Hindi transcript directly...")
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['hi'])
            logger.info(f"SUCCESS: Got Hindi transcript with {len(transcript)} entries")
            return transcript, 'hi'
        except Exception as hi_error:
            logger.warning(f"Hindi transcript failed: {hi_error}")
        
        # List available transcripts using correct method
        try:
            logger.info("Listing available transcripts...")
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            logger.info("Available transcripts:")
            
            available_transcripts = []
            for transcript_info in transcript_list:
                logger.info(f"  - {transcript_info.language_code}: {transcript_info.language} (Generated: {transcript_info.is_generated}, Translatable: {transcript_info.is_translatable})")
                available_transcripts.append(transcript_info)
            
            # Try to fetch each transcript
            for transcript_info in available_transcripts:
                try:
                    logger.info(f"\nTrying to fetch transcript: {transcript_info.language_code}")
                    transcript = transcript_info.fetch()
                    logger.info(f"SUCCESS: Fetched {len(transcript)} entries")
                    logger.info("First 3 entries:")
                    for i, entry in enumerate(transcript[:3]):
                        logger.info(f"  {i+1}: {entry}")
                    
                    return transcript, transcript_info.language_code
                    
                except Exception as e:
                    logger.error(f"FAILED to fetch {transcript_info.language_code}: {e}")
                    continue
            
        except Exception as list_error:
            logger.error(f"Failed to list transcripts: {list_error}")
        
        logger.error("No transcripts could be fetched")
        return None, None
        
    except Exception as e:
        logger.error(f"Error in transcript access: {e}")
        return None, None

def test_simple_fetch(video_id):
    """Test simple transcript fetch"""
    try:
        logger.info(f"Testing simple fetch for video: {video_id}")
        
        # Try different language codes
        language_codes = ['en', 'hi', 'en-US', 'en-GB']
        
        for lang_code in language_codes:
            try:
                logger.info(f"Trying language: {lang_code}")
                transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang_code])
                logger.info(f"SUCCESS: Got transcript in {lang_code} with {len(transcript)} entries")
                logger.info("First entry:")
                logger.info(f"  {transcript[0]}")
                return transcript, lang_code
            except Exception as e:
                logger.warning(f"Failed for {lang_code}: {e}")
                continue
        
        logger.error("All simple fetch attempts failed")
        return None, None
        
    except Exception as e:
        logger.error(f"Simple fetch test failed: {e}")
        return None, None

if __name__ == "__main__":
    video_id = "a3VLxRfWBbA"
    
    print("=== Testing simple transcript fetch ===")
    transcript, lang_code = test_simple_fetch(video_id)
    
    if transcript:
        print(f"\n✅ Successfully got transcript in {lang_code}")
        print(f"Total entries: {len(transcript)}")
    else:
        print("\n❌ Simple fetch failed")
    
    print("\n=== Testing with transcript listing ===")
    transcript, lang_code = debug_transcript_correct_api(video_id)
    
    if transcript:
        print(f"\n✅ Successfully got transcript in {lang_code}")
        print(f"Total entries: {len(transcript)}")
    else:
        print("\n❌ Could not get any transcript")