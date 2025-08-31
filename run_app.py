# run_app.py
import os
import sys
import subprocess
import webbrowser
import time
from threading import Timer

def check_requirements():
    """Check if all requirements are met"""
    print("🔍 Checking requirements...")
    
    # Check if required files exist
    required_files = [
        'app_improved.py',
        'config.py', 
        'models.py',
        'services.py',
        'requirements.txt',
        '.env',
        'index.html',
        'api.js'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        print("Please ensure all files are in the current directory")
        return False
    
    print("✅ All required files found")
    return True

def check_env_config():
    """Check if .env file is properly configured"""
    print("🔧 Checking configuration...")
    
    try:
        with open('.env', 'r') as f:
            content = f.read()
        
        # Check for placeholder values
        placeholders = [
            'your_mysql_password',
            'your_openai_api_key_here',
            'your_secret_key_change_this_in_production'
        ]
        
        issues = []
        for placeholder in placeholders:
            if placeholder in content:
                issues.append(placeholder)
        
        if issues:
            print("⚠️  Configuration issues found:")
            for issue in issues:
                print(f"   - Please replace: {issue}")
            
            print("\n📝 Please update your .env file with actual values:")
            print("   - MySQL password")
            print("   - OpenAI API key")
            print("   - Secret key for JWT")
            return False
        
        print("✅ Configuration looks good")
        return True
        
    except Exception as e:
        print(f"❌ Error reading .env file: {e}")
        return False

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing dependencies...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("✅ Dependencies installed")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        print("Try running: pip install -r requirements.txt")
        return False

def test_database_connection():
    """Test database connection"""
    print("🗄️  Testing database connection...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        import mysql.connector
        from config import Config
        
        connection = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            database=Config.MYSQL_DATABASE,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD
        )
        
        if connection.is_connected():
            print("✅ Database connection successful")
            connection.close()
            return True
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\n🔧 Please check:")
        print("   - MySQL server is running")
        print("   - Database 'recipe_recommender' exists")
        print("   - Credentials in .env file are correct")
        return False

def test_openai_connection():
    """Test OpenAI API key"""
    print("🤖 Testing OpenAI connection...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        import openai
        from config import Config
        
        openai.api_key = Config.OPENAI_API_KEY
        
        # Test with a simple completion
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5
        )
        
        print("✅ OpenAI API connection successful")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI API test failed: {e}")
        print("\n🔧 Please check:")
        print("   - OpenAI API key is correct")
        print("   - You have API credits available")
        print("   - Key has proper permissions")
        return False

def open_browser():
    """Open browser to the application"""
    print("🌐 Opening application in browser...")
    
    # Wait a bit for the server to start
    time.sleep(2)
    
    try:
        webbrowser.open('http://localhost:8080')
        print("✅ Browser opened")
    except Exception as e:
        print(f"⚠️  Could not open browser automatically: {e}")
        print("Please manually open: http://localhost:8080")

def start_backend():
    """Start the Flask backend"""
    print("🚀 Starting Flask backend...")
    
    try:
        # Start Flask app in a subprocess
        backend_process = subprocess.Popen([
            sys.executable, 'app_improved.py'
        ])
        
        print("✅ Backend started on http://localhost:5000")
        return backend_process
        
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return None

def start_frontend():
    """Start frontend server"""
    print("🎨 Starting frontend server...")
    
    try:
        # Start simple HTTP server for frontend
        frontend_process = subprocess.Popen([
            sys.executable, '-m', 'http.server', '8080'
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        print("✅ Frontend started on http://localhost:8080")
        return frontend_process
        
    except Exception as e:
        print(f"❌ Failed to start frontend: {e}")
        return None

def main():
    """Main application runner"""
    print("🍳 Recipe Recommender App Launcher")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        return False
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Check configuration
    if not check_env_config():
        print("\n❌ Please configure your .env file and run again")
        return False
    
    # Test connections
    if not test_database_connection():
        return False
    
    if not test_openai_connection():
        print("⚠️  OpenAI test failed, but app will still work with fallback recipes")
    
    print("\n🚀 Starting application...")
    
    # Start backend
    backend_process = start_backend()
    if not backend_process:
        return False
    
    # Start frontend
    frontend_process = start_frontend()
    if not frontend_process:
        backend_process.terminate()
        return False
    
    # Open browser after a delay
    Timer(3.0, open_browser).start()
    
    print("\n✨ Application is running!")
    print("📱 Frontend: http://localhost:8080")
    print("🔧 Backend API: http://localhost:5000")
    print("\nPress Ctrl+C to stop the application")
    
    try:
        # Wait for user to stop
        backend_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping application...")
        backend_process.terminate()
        frontend_process.terminate()
        print("✅ Application stopped")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            print("\n❌ Failed to start application")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)