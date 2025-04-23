#!/usr/bin/env python
import os
import shutil
import subprocess
import sys
from pathlib import Path

def check_python_version():
    """Check if Python version is 3.8 or higher."""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required.")
        sys.exit(1)
    print("✅ Python version check passed")

def create_virtual_environment():
    """Create a virtual environment for the project."""
    if os.path.exists(".venv"):
        print("Virtual environment already exists.")
        return
    
    print("Creating virtual environment...")
    subprocess.run([sys.executable, "-m", "venv", ".venv"], check=True)
    print("✅ Virtual environment created")

def install_dependencies():
    """Install project dependencies."""
    print("Installing dependencies...")
    
    # Determine the pip path based on the operating system
    pip_path = ".venv/bin/pip" if os.name != "nt" else ".venv\\Scripts\\pip"
    
    # Install dependencies
    subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True)
    print("✅ Dependencies installed")

def setup_env_file():
    """Set up the .env file from the example if it doesn't exist."""
    if not os.path.exists(".env") and os.path.exists(".env.example"):
        print("Creating .env file from .env.example...")
        shutil.copy(".env.example", ".env")
        print("✅ .env file created. Please edit it with your actual credentials.")
    elif os.path.exists(".env"):
        print(".env file already exists.")
    else:
        print("Warning: .env.example file not found. Please create a .env file manually.")

def setup_whatsapp_mcp():
    """Provide instructions for setting up WhatsApp MCP."""
    print("\n📱 WhatsApp MCP Setup Instructions 📱")
    print("1. Clone the WhatsApp MCP repository:")
    print("   git clone https://github.com/lharries/whatsapp-mcp.git")
    print("2. Follow the setup instructions in the WhatsApp MCP README.md")
    print("3. Start the WhatsApp bridge:")
    print("   cd whatsapp-bridge")
    print("   go run main.go")
    print("4. Scan the QR code with your WhatsApp mobile app")
    print("5. Configure the MCP server for your AI assistant")

def main():
    """Main setup function."""
    print("\n🔹🔹🔹 WhatsApp Diamond Sales AI Agent Setup 🔹🔹🔹\n")
    
    # Run setup steps
    check_python_version()
    create_virtual_environment()
    install_dependencies()
    setup_env_file()
    setup_whatsapp_mcp()
    
    print("\n✨ Setup complete! ✨")
    print("\nNext steps:")
    print("1. Edit the .env file with your Supabase and OpenAI credentials")
    print("2. Set up the WhatsApp MCP server following the instructions above")
    print("3. Run the agent with: python main.py")
    print("\nHappy selling! 💎\n")

if __name__ == "__main__":
    main()