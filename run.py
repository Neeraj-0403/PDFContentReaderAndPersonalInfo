#!/usr/bin/env python3
"""
Simple script to run the Flask PDF Reader application
"""

import os
import sys
from app import app

if __name__ == '__main__':
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("⚠️  Warning: .env file not found!")
        print("Please create a .env file with your OPENAI_API_KEY")
        print("Example: OPENAI_API_KEY=your_api_key_here")
        sys.exit(1)
    
    print("🚀 Starting PDF Reader Application...")
    print("📱 Open your browser and go to: http://localhost:5000")
    print("🛑 Press Ctrl+C to stop the server")
    
    app.run(debug=True, host='0.0.0.0', port=5000)