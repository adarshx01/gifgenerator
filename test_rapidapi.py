import http.client
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_rapidapi_transcript():
    """Test the RapidAPI YouTube Transcriptor"""
    try:
        video_id = "a3VLxRfWBbA"  # Your test video
        
        conn = http.client.HTTPSConnection("youtube-transcriptor.p.rapidapi.com")
        headers = {
            'x-rapidapi-key': "ea168c620amshdb607f4662336e0p12b946jsn3680b59662a7",
            'x-rapidapi-host': "youtube-transcriptor.p.rapidapi.com"
        }
        
        # Test with Hindi
        logger.info(f"Testing Hindi transcript for video: {video_id}")
        conn.request("GET", f"/transcript?video_id={video_id}&lang=hi", headers=headers)
        res = conn.getresponse()
        data = res.read()
        
        logger.info(f"Response status: {res.status}")
        logger.info(f"Response reason: {res.reason}")
        
        if res.status == 200:
            response_data = json.loads(data.decode("utf-8"))
            logger.info(f"Response type: {type(response_data)}")
            
            if response_data and len(response_data) > 0:
                video_info = response_data[0]
                logger.info(f"Video title: {video_info.get('title', 'N/A')}")
                logger.info(f"Available languages: {video_info.get('availableLangs', [])}")
                
                transcription = video_info.get('transcription', [])
                logger.info(f"Transcription entries: {len(transcription)}")
                
                if transcription:
                    logger.info("First 3 transcription entries:")
                    for i, entry in enumerate(transcription[:3]):
                        logger.info(f"  {i+1}: {entry}")
                    
                    return True, transcription
                else:
                    logger.warning("No transcription data found")
                    return False, None
            else:
                logger.error("Empty response data")
                return False, None
        else:
            logger.error(f"API request failed: {res.status} - {res.reason}")
            logger.error(f"Response: {data.decode('utf-8')}")
            return False, None
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False, None

if __name__ == "__main__":
    success, transcript = test_rapidapi_transcript()
    
    if success:
        print("✅ RapidAPI test successful!")
        print(f"Got {len(transcript)} transcript entries")
    else:
        print("❌ RapidAPI test failed")