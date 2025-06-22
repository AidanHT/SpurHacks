#!/usr/bin/env python3
"""
Frontend server starter for Promptly
"""

import os
import sys
import subprocess
from pathlib import Path

def run_frontend():
    """Start the React frontend development server"""
    frontend_dir = Path(__file__).parent / "frontend"
    
    if not frontend_dir.exists():
        print("❌ Frontend directory not found!")
        sys.exit(1)
    
    # Check if node_modules exists
    node_modules = frontend_dir / "node_modules"
    if not node_modules.exists():
        print("📦 Installing frontend dependencies...")
        try:
            subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies. Make sure Node.js and npm are installed.")
            sys.exit(1)
    
    print("🚀 Starting Promptly Frontend Server...")
    print("📍 Frontend running at: http://localhost:5173")
    print("🔧 Development mode with hot reload")
    print()
    
    # Start the development server
    try:
        subprocess.run(["npm", "run", "dev"], cwd=frontend_dir, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting frontend server: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Frontend server stopped.")

if __name__ == "__main__":
    run_frontend() 