#!/usr/bin/env python3
"""
Test script cho No-DB File Management API
==========================================
Test các endpoints: upload, map, download, status

Usage:
    python scripts/test_no_db_api.py [--file <path_to_excel_file>]
"""

import sys
import os
import requests
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1/no-db-files"


def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_upload(file_path: str):
    """Test upload endpoint"""
    print(f"\n📤 Testing upload endpoint with file: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"   ❌ File not found: {file_path}")
        return None
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            data = {'station': 'HAN'}
            response = requests.post(f"{API_BASE}/upload", files=files, data=data, timeout=30)
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Upload successful!")
            print(f"   Upload ID: {result.get('upload_id')}")
            print(f"   Filename: {result.get('filename')}")
            return result.get('upload_id')
        else:
            print(f"   ❌ Upload failed: {response.text}")
            return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None


def test_map(upload_id: str, station: str = "HAN", download_mode: str = "styled"):
    """Test map endpoint"""
    print(f"\n🔄 Testing map endpoint...")
    print(f"   Upload ID: {upload_id}")
    print(f"   Station: {station}")
    print(f"   Mode: {download_mode}")
    print(f"   ⏳ This may take several minutes for large files...")
    
    try:
        data = {
            'upload_id': upload_id,
            'station': station,
            'download_mode': download_mode
        }
        # Increase timeout to 5 minutes (300 seconds) for large files
        response = requests.post(f"{API_BASE}/map", data=data, timeout=300)
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Mapping successful!")
            print(f"   File ID: {result.get('file_id')}")
            print(f"   Download URL: {result.get('download_url')}")
            return result.get('file_id')
        else:
            print(f"   ❌ Mapping failed: {response.text}")
            return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None


def test_status(file_id: str):
    """Test status endpoint"""
    print(f"\n📊 Testing status endpoint...")
    print(f"   File ID: {file_id}")
    
    try:
        response = requests.get(f"{API_BASE}/status/{file_id}", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Status retrieved!")
            print(f"   Status: {result.get('status')}")
            print(f"   Station: {result.get('station')}")
            print(f"   Created: {result.get('created_at')}")
            return True
        else:
            print(f"   ❌ Status check failed: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_download(file_id: str, output_path: str = None):
    """Test download endpoint"""
    print(f"\n📥 Testing download endpoint...")
    print(f"   File ID: {file_id}")
    
    if output_path is None:
        output_path = f"test_output_{file_id}.xlsx"
    
    try:
        # Increase timeout for large file downloads
        response = requests.get(f"{API_BASE}/download/{file_id}", timeout=300, stream=True)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            # Save file
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            file_size = os.path.getsize(output_path)
            print(f"   ✅ Download successful!")
            print(f"   Saved to: {output_path}")
            print(f"   Size: {file_size} bytes")
            
            # Verify file was deleted (status should return 404)
            import time
            time.sleep(1)  # Wait a bit for background task
            status_response = requests.get(f"{API_BASE}/status/{file_id}", timeout=5)
            if status_response.status_code == 404:
                print(f"   ✅ File deleted after download (as expected)")
            else:
                print(f"   ⚠️  File still exists (may take a moment to delete)")
            
            return True
        else:
            print(f"   ❌ Download failed: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def main():
    """Main test function"""
    import argparse
    
    global BASE_URL, API_BASE
    
    parser = argparse.ArgumentParser(description='Test No-DB File Management API')
    parser.add_argument('--file', type=str, help='Path to Excel file to test with')
    parser.add_argument('--url', type=str, default='http://localhost:8000', help='Base URL (default: http://localhost:8000)')
    args = parser.parse_args()
    
    BASE_URL = args.url
    API_BASE = f"{BASE_URL}/api/v1/no-db-files"
    
    print("=" * 60)
    print("🧪 No-DB File Management API Test")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}")
    print()
    
    # Test health
    if not test_health():
        print("\n❌ Server không chạy hoặc health check failed!")
        print("   Hãy chạy server trước: uvicorn app.main:app --reload")
        sys.exit(1)
    
    # Find test file
    test_file = args.file
    if not test_file:
        # Try to find a test file in uploads directory
        uploads_dir = Path(__file__).parent.parent / "uploads" / "uploads"
        if uploads_dir.exists():
            xlsx_files = list(uploads_dir.glob("*.xlsx"))
            if xlsx_files:
                test_file = str(xlsx_files[0])
                print(f"\n📁 Using test file: {test_file}")
    
    if not test_file or not os.path.exists(test_file):
        print("\n⚠️  Không tìm thấy file test!")
        print("   Usage: python scripts/test_no_db_api.py --file <path_to_excel_file>")
        print("   Hoặc đặt file .xlsx trong thư mục uploads/uploads/")
        sys.exit(1)
    
    # Run tests
    print("\n" + "=" * 60)
    print("🚀 Starting API Tests")
    print("=" * 60)
    
    # 1. Upload
    upload_id = test_upload(test_file)
    if not upload_id:
        print("\n❌ Upload test failed!")
        sys.exit(1)
    
    # 2. Map
    file_id = test_map(upload_id, station="HAN", download_mode="styled")
    if not file_id:
        print("\n❌ Map test failed!")
        sys.exit(1)
    
    # 3. Status
    test_status(file_id)
    
    # 4. Download
    output_file = f"test_output_{file_id}.xlsx"
    if test_download(file_id, output_file):
        print(f"\n✅ All tests passed!")
        print(f"   Output file: {output_file}")
    else:
        print("\n❌ Download test failed!")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ Test completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()

