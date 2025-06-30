from youtube_transcript_api import YouTubeTranscriptApi
import re

def extract_youtube_id(url: str) -> str:
    """Extract YouTube video ID from URL"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
        r'youtube\.com\/watch\?.*v=([^&\n?#]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError("Invalid YouTube URL")

def test_transcript_with_translation(url):
    try:
        video_id = extract_youtube_id(url)
        print(f"Video ID: {video_id}")
        
        # Try to get English transcript first
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'en-US', 'en-GB'])
            print(f"Found English transcript with {len(transcript)} entries")
            print("First few entries:")
            for i, entry in enumerate(transcript[:3]):
                print(f"  {i+1}: {entry}")
            return True
        except Exception as e:
            print(f"No English transcript: {e}")
            
            # List available transcripts
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            print("\nAvailable transcripts:")
            
            # Try to find translatable transcript
            for transcript_info in transcript_list:
                print(f"  - {transcript_info.language_code}: {transcript_info.language} (Generated: {transcript_info.is_generated}, Translatable: {transcript_info.is_translatable})")
                
                if transcript_info.is_translatable and transcript_info.language_code != 'en':
                    try:
                        print(f"\nTrying to translate {transcript_info.language_code} to English...")
                        translated = transcript_info.translate('en')
                        transcript = translated.fetch()
                        print(f"Successfully translated! Got {len(transcript)} entries")
                        print("First few translated entries:")
                        for i, entry in enumerate(transcript[:3]):
                            print(f"  {i+1}: {entry}")
                        return True
                    except Exception as translate_error:
                        print(f"Translation failed: {translate_error}")
                        continue
            
            # If translation fails, try to get original transcript
            for transcript_info in transcript_list:
                if transcript_info.is_generated:
                    try:
                        transcript = transcript_info.fetch()
                        print(f"\nGot original transcript in {transcript_info.language_code} with {len(transcript)} entries")
                        print("First few entries (original language):")
                        for i, entry in enumerate(transcript[:3]):
                            print(f"  {i+1}: {entry}")
                        return True
                    except Exception as fetch_error:
                        print(f"Failed to fetch {transcript_info.language_code}: {fetch_error}")
                        continue
        
        return False
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_url = "https://youtu.be/a3VLxRfWBbA?si=5HD9gLCIfsMT-L8c"
    print("Testing transcript retrieval and translation...")
    test_transcript_with_translation(test_url)