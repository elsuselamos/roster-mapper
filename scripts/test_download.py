#!/usr/bin/env python3
"""
Test script để verify download functionality
Chạy sau khi server đã start: uvicorn app.main:app --reload
"""

import requests
import sys
from pathlib import Path
import time

BASE_URL = "http://localhost:8000"
TEST_FILE = None  # Set path to test Excel file if needed


def test_status_check(session_id: str):
    """Test status check API"""
    print(f"\n🔍 Testing status check API...")
    url = f"{BASE_URL}/api/v1/results/status"
    params = {"session_id": session_id}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        print(f"✅ Status: {data.get('status')}")
        print(f"   Message: {data.get('message')}")
        
        if data.get('status') == 'completed':
            results = data.get('results', {}).get('files', [])
            print(f"   Files processed: {len(results)}")
            for file_info in results:
                print(f"   - {file_info.get('filename')} ({file_info.get('file_id')})")
                print(f"     Styled: {file_info.get('download_url_styled')}")
                print(f"     Plain: {file_info.get('download_url_plain')}")
        
        return data
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_download(file_id: str, format_type: str = "styled"):
    """Test download endpoint"""
    print(f"\n📥 Testing download: file_id={file_id}, format={format_type}")
    url = f"{BASE_URL}/api/v1/download/{file_id}"
    params = {"format": format_type}
    
    try:
        response = requests.get(url, params=params, stream=True)
        response.raise_for_status()
        
        # Save file
        filename = f"test_download_{file_id}_{format_type}.xlsx"
        with open(filename, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        file_size = Path(filename).stat().st_size
        print(f"✅ Download successful: {filename} ({file_size} bytes)")
        return filename
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        if e.response.status_code == 404:
            print(f"   File not found. Check if file was processed correctly.")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_full_flow():
    """Test full flow: upload → process → download"""
    print("\n" + "="*60)
    print("🧪 Testing Full Flow")
    print("="*60)
    
    # Step 1: Check if we have a test file
    if not TEST_FILE or not Path(TEST_FILE).exists():
        print("⚠️  No test file provided. Skipping upload test.")
        print("   To test upload, set TEST_FILE variable in script.")
        return
    
    # Step 2: Upload file
    print("\n1️⃣  Uploading file...")
    try:
        with open(TEST_FILE, "rb") as f:
            files = {"files": (Path(TEST_FILE).name, f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            response = requests.post(f"{BASE_URL}/upload", files=files)
            response.raise_for_status()
            print("✅ Upload successful (redirected to select-sheets)")
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return
    
    print("\n⚠️  Note: Full flow requires manual interaction:")
    print("   1. Go to http://localhost:8000/upload")
    print("   2. Upload file, select sheets, preview")
    print("   3. Start processing")
    print("   4. Get session_id from results page")
    print("   5. Run: python scripts/test_download.py <session_id>")


def main():
    """Main test function"""
    if len(sys.argv) > 1:
        # Test with provided session_id
        session_id = sys.argv[1]
        print(f"🧪 Testing with session_id: {session_id}")
        
        # Test status check
        status_data = test_status_check(session_id)
        
        if status_data and status_data.get('status') == 'completed':
            results = status_data.get('results', {}).get('files', [])
            
            if results:
                # Test download for first file
                file_info = results[0]
                file_id = file_info.get('file_id')
                
                # Test styled format
                test_download(file_id, "styled")
                
                # Test plain format
                test_download(file_id, "plain")
            else:
                print("⚠️  No files in results")
        else:
            print("⚠️  Processing not completed or session not found")
    else:
        # Run full flow test
        test_full_flow()
        
        print("\n" + "="*60)
        print("📝 Usage:")
        print("   python scripts/test_download.py <session_id>")
        print("   Example: python scripts/test_download.py session_1234567890")
        print("="*60)


if __name__ == "__main__":
    main()


