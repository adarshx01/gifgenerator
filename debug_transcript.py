from youtube_transcript_api import YouTubeTranscriptApi
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_transcript(video_id):
    """Debug transcript access for a specific video"""
    try:
        logger.info(f"Debugging transcript access for video: {video_id}")
        
        # List available transcripts
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
                    
                # If this is the first successful one, break
                return transcript, transcript_info.language_code
                
            except Exception as e:
                logger.error(f"FAILED to fetch {transcript_info.language_code}: {e}")
                continue
        
        logger.error("No transcripts could be fetched")
        return None, None
        
    except Exception as e:
        logger.error(f"Error listing transcripts: {e}")
        return None, None

if __name__ == "__main__":
    video_id = "a3VLxRfWBbA"
    transcript, lang_code = debug_transcript(video_id)
    
    if transcript:
        print(f"\n✅ Successfully got transcript in {lang_code}")
        print(f"Total entries: {len(transcript)}")
    else:
        print("\n❌ Could not get any transcript")