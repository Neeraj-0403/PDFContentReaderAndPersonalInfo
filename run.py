#!/usr/bin/env python3
"""
Simple script to run the FastAPI PDF Reader application
"""

import os
import sys
import uvicorn

if __name__ == '__main__':
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("⚠️  Warning: .env file not found!")
        print("Please create a .env file with your OPENAI_API_KEY")
        print("Example: OPENAI_API_KEY=your_api_key_here")
        sys.exit(1)
    
    print("🚀 Starting FastAPI PDF Reader Application...")
    print("📱 Open your browser and go to: http://localhost:8000")
    print("🛑 Press Ctrl+C to stop the server")
    
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)