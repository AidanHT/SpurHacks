#!/usr/bin/env python3
"""
Docker Management Script for Promptly
Easily start development or production Docker environments
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, cwd=None):
    """Run a shell command and print output"""
    print(f"🔧 Running: {cmd}")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            check=True,
            text=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed with exit code {e.returncode}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Manage Promptly Docker containers")
    parser.add_argument(
        "command",
        choices=["dev", "prod", "stop", "clean", "logs", "build"],
        help="Command to execute"
    )
    parser.add_argument(
        "--service",
        help="Specific service to target (api, web, mongo, redis, minio)"
    )
    
    args = parser.parse_args()
    
    # Change to infra directory
    infra_dir = Path(__file__).parent / "infra"
    if not infra_dir.exists():
        print("❌ infra directory not found!")
        sys.exit(1)
    
    print("🚀 Promptly Docker Manager")
    print(f"📍 Working directory: {infra_dir}")
    print()
    
    if args.command == "dev":
        print("🔧 Starting development environment...")
        print("   - Frontend: http://localhost:5173 (with hot reload)")
        print("   - Backend: http://localhost:8000 (with auto-reload)")
        print("   - API Docs: http://localhost:8000/docs")
        print()
        
        cmd = "docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build"
        if args.service:
            cmd += f" {args.service}"
        
        success = run_command(cmd, cwd=infra_dir)
        if not success:
            print("💡 Make sure Docker Desktop is running!")
    
    elif args.command == "prod":
        print("🚀 Starting production environment...")
        print("   - Frontend: http://localhost:3000")
        print("   - Backend: http://localhost:8000")
        print("   - API Docs: http://localhost:8000/docs")
        print()
        
        cmd = "docker-compose up --build -d"
        if args.service:
            cmd += f" {args.service}"
            
        success = run_command(cmd, cwd=infra_dir)
        if success:
            print("✅ Production environment started!")
            print("🔍 Check status with: python run_docker.py logs")
    
    elif args.command == "stop":
        print("🛑 Stopping all containers...")
        
        cmd = "docker-compose -f docker-compose.yml -f docker-compose.dev.yml down"
        if args.service:
            cmd = f"docker-compose stop {args.service}"
            
        success = run_command(cmd, cwd=infra_dir)
        if success:
            print("✅ Containers stopped!")
    
    elif args.command == "clean":
        print("🧹 Cleaning up containers and volumes...")
        
        commands = [
            "docker-compose -f docker-compose.yml -f docker-compose.dev.yml down -v",
            "docker system prune -f",
        ]
        
        for cmd in commands:
            run_command(cmd, cwd=infra_dir)
        
        print("✅ Cleanup complete!")
    
    elif args.command == "logs":
        print("📋 Showing container logs...")
        
        cmd = "docker-compose logs"
        if args.service:
            cmd += f" {args.service}"
        else:
            cmd += " --tail=50 -f"
            
        run_command(cmd, cwd=infra_dir)
    
    elif args.command == "build":
        print("🔨 Building containers...")
        
        cmd = "docker-compose build"
        if args.service:
            cmd += f" {args.service}"
            
        success = run_command(cmd, cwd=infra_dir)
        if success:
            print("✅ Build complete!")


if __name__ == "__main__":
    main() 