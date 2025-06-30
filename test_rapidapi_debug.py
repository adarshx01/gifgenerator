import http.client
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_rapidapi_connection():
    """Test RapidAPI connection with detailed debugging"""
    try:
        video_id = "a3VLxRfWBbA"
        
        # Test connection first
        logger.info("Testing HTTPS connection...")
        conn = http.client.HTTPSConnection("youtube-transcriptor.p.rapidapi.com")
        
        headers = {
            'x-rapidapi-key': "ea168c620amshdb607f4662336e0p12b946jsn3680b59662a7",
            'x-rapidapi-host': "youtube-transcriptor.p.rapidapi.com"
        }
        
        logger.info(f"Headers: {headers}")
        logger.info(f"Making request to /transcript?video_id={video_id}&lang=en")
        
        # Make request
        conn.request("GET", f"/transcript?video_id={video_id}&lang=en", headers=headers)
        res = conn.getresponse()
        data = res.read()
        
        logger.info(f"Response status: {res.status}")
        logger.info(f"Response reason: {res.reason}")
        logger.info(f"Response headers: {dict(res.getheaders())}")
        logger.info(f"Response data length: {len(data) if data else 0}")
        
        if data:
            try:
                decoded_data = data.decode("utf-8")
                logger.info(f"Response data (first 500 chars): {decoded_data[:500]}")
                
                # Try to parse JSON
                if res.status == 200:
                    response_json = json.loads(decoded_data)
                    logger.info(f"Parsed JSON successfully")
                    logger.info(f"JSON structure: {json.dumps(response_json, indent=2)}")
                    return True, response_json
                else:
                    logger.error(f"API returned error status: {res.status}")
                    return False, decoded_data
                    
            except UnicodeDecodeError as e:
                logger.error(f"Failed to decode response: {e}")
                return False, None
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON: {e}")
                return False, decoded_data
        else:
            logger.error("Empty response received")
            return False, None
            
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        logger.error(f"Error type: {type(e)}")
        return False, str(e)

def test_alternative_request():
    """Test using requests library as alternative"""
    try:
        import requests
        
        url = "https://youtube-transcriptor.p.rapidapi.com/transcript"
        querystring = {"video_id": "a3VLxRfWBbA", "lang": "en"}
        headers = {
            "x-rapidapi-key": "ea168c620amshdb607f4662336e0p12b946jsn3680b59662a7",
            "x-rapidapi-host": "youtube-transcriptor.p.rapidapi.com"
        }
        
        logger.info("Testing with requests library...")
        response = requests.get(url, headers=headers, params=querystring, timeout=30)
        
        logger.info(f"Requests response status: {response.status_code}")
        logger.info(f"Requests response headers: {dict(response.headers)}")
        logger.info(f"Requests response content length: {len(response.content)}")
        
        if response.status_code == 200:
            logger.info(f"Response text (first 500 chars): {response.text[:500]}")
            try:
                response_json = response.json()
                logger.info("JSON parsed successfully with requests")
                return True, response_json
            except:
                logger.error("Failed to parse JSON with requests")
                return False, response.text
        else:
            logger.error(f"Requests failed with status: {response.status_code}")
            logger.error(f"Response text: {response.text}")
            return False, response.text
            
    except ImportError:
        logger.error("Requests library not available")
        return False, "requests not installed"
    except Exception as e:
        logger.error(f"Requests test failed: {e}")
        return False, str(e)

if __name__ == "__main__":
    print("=== Testing RapidAPI with http.client ===")
    success1, result1 = test_rapidapi_connection()
    
    print("\n=== Testing RapidAPI with requests library ===")
    success2, result2 = test_alternative_request()
    
    if success1:
        print("\n✅ http.client test successful!")
    else:
        print(f"\n❌ http.client test failed: {result1}")
        
    if success2:
        print("\n✅ requests test successful!")
    else:
        print(f"\n❌ requests test failed: {result2}")