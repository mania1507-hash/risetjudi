import requests
import json

def test_server():
    base_url = "http://127.0.0.1:5000"
    
    print("🔍 Testing Server Connection...")
    
    # Test endpoints satu per satu
    endpoints = [
        ("/", "Home page"),
        ("/health", "Health check"), 
        ("/api/test", "API test"),
        ("/api/detect-video", "Video detection (GET)"),
        ("/wrong-endpoint", "Non-existent endpoint (should 404)")
    ]
    
    for endpoint, description in endpoints:
        print(f"\n📡 Testing: {endpoint} - {description}")
        
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   ✅ SUCCESS: {data}")
                except:
                    print(f"   ⚠️  Not JSON: {response.text[:100]}")
            elif response.status_code == 404:
                try:
                    data = response.json()
                    print(f"   🔍 404 Response: {data}")
                except:
                    print(f"   ❌ 404 - Not JSON: {response.text[:100]}")
            else:
                print(f"   ❌ Unexpected status: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ CONNECTION ERROR: Server not running")
        except requests.exceptions.Timeout:
            print(f"   ❌ TIMEOUT: Server not responding")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")

def test_video_upload():
    print(f"\n🎥 Testing Video Upload...")
    
    # Buat file test kecil
    test_content = b"fake video content" * 1000  # 17KB
    with open('test_video.mp4', 'wb') as f:
        f.write(test_content)
    
    try:
        with open('test_video.mp4', 'rb') as f:
            files = {'video': ('test.mp4', f, 'video/mp4')}
            response = requests.post(
                "http://127.0.0.1:5000/api/detect-video",
                files=files,
                timeout=10
            )
        
        print(f"   Upload Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ UPLOAD SUCCESS: {data}")
        else:
            print(f"   ❌ UPLOAD FAILED: {response.text}")
            
    except Exception as e:
        print(f"   ❌ UPLOAD ERROR: {e}")
    
    # Cleanup
    import os
    if os.path.exists('test_video.mp4'):
        os.remove('test_video.mp4')

if __name__ == "__main__":
    test_server()
    test_video_upload()