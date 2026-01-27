"""
Test script to verify video analysis API with no_idcard.mp4
"""
import requests
import json

# Configuration
API_URL = "http://127.0.0.1:8081"
VIDEO_PATH = "no_idcard.mp4"

def test_video_analysis():
    print("=" * 60)
    print("Testing Video Analysis API")
    print("=" * 60)
    
    # Check if server is running
    try:
        response = requests.get(f"{API_URL}/")
        print(f"✓ Server Status: {response.json()}")
    except Exception as e:
        print(f"✗ Server not reachable: {e}")
        return
    
    print("\n" + "=" * 60)
    print("Uploading video for analysis...")
    print("=" * 60)
    
    # Upload video
    try:
        with open(VIDEO_PATH, 'rb') as video_file:
            files = {'file': (VIDEO_PATH, video_file, 'video/mp4')}
            response = requests.post(
                f"{API_URL}/analyze_video",
                files=files,
                timeout=300  # 5 minutes timeout
            )
        
        if response.status_code == 200:
            results = response.json()
            print("\n✓ Analysis Complete!")
            print("\n" + "=" * 60)
            print("RESULTS")
            print("=" * 60)
            
            print(f"\nFilename: {results.get('filename')}")
            print(f"Total Frames Processed: {results.get('total_frames_processed')}")
            print(f"Violations Detected: {results.get('violations_detected')}")
            
            violations = results.get('violations', [])
            
            if violations:
                print("\n" + "=" * 60)
                print("VIOLATORS DETECTED")
                print("=" * 60)
                
                for i, violation in enumerate(violations, 1):
                    print(f"\n--- Violator #{i} ---")
                    print(f"Name: {violation.get('name')}")
                    print(f"Track ID: {violation.get('track_id')}")
                    print(f"Timestamp: {violation.get('timestamp')}s")
                    print(f"Frame Number: {violation.get('frame_number')}")
                    print(f"Violation Type: {violation.get('violation_type')}")
                    print(f"Image Path: {violation.get('image_path')}")
                    
                    # Check if Raju was detected
                    if violation.get('name') == 'raju':
                        print("✓ RAJU DETECTED CORRECTLY!")
                    elif violation.get('name') == 'Unknown':
                        print("⚠ Person not in database (Unknown)")
            else:
                print("\n⚠ No violations detected in video")
            
            print("\n" + "=" * 60)
            print("Full Response:")
            print("=" * 60)
            print(json.dumps(results, indent=2))
            
        else:
            print(f"\n✗ Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"\n✗ Upload failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_video_analysis()
