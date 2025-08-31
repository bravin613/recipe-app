# setup.py
import os
import sys
import subprocess
import mysql.connector
from mysql.connector import Error

def check_python_version():
    """Check if Python version is 3.7 or higher"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        return False
    print(f"✅ Python {sys.version.split()[0]} detected")
    return True

def install_requirements():
    """Install required Python packages"""
    try:
        print("📦 Installing Python requirements...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install requirements")
        return False

def create_env_file():
    """Create .env file if it doesn't exist"""
    if os.path.exists('.env'):
        print("✅ .env file already exists")
        return True
    
    print("📝 Creating .env file...")
    env_content = """# Database Configuration
MYSQL_HOST=localhost
MYSQL_DATABASE=recipe_recommender
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Flask Configuration
SECRET_KEY=your_secret_key_change_this_in_production
FLASK_ENV=development
FLASK_DEBUG=True

# JWT Configuration
JWT_EXPIRATION_DAYS=7
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ .env file created")
        print("⚠️  Please update the .env file with your actual credentials")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def test_mysql_connection():
    """Test MySQL connection"""
    print("🔍 Testing MySQL connection...")
    
    # Get credentials from user
    host = input("MySQL Host (localhost): ").strip() or 'localhost'
    user = input("MySQL User (root): ").strip() or 'root'
    password = input("MySQL Password: ").strip()
    
    try:
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password
        )
        
        if connection.is_connected():
            print("✅ MySQL connection successful")
            
            # Create database
            cursor = connection.cursor()
            cursor.execute("CREATE DATABASE IF NOT EXISTS recipe_recommender")
            print("✅ Database 'recipe_recommender' created/verified")
            
            cursor.close()
            connection.close()
            
            # Update .env file with working credentials
            update_env_mysql(host, user, password)
            return True
            
    except Error as e:
        print(f"❌ MySQL connection failed: {e}")
        return False

def update_env_mysql(host, user, password):
    """Update .env file with MySQL credentials"""
    try:
        with open('.env', 'r') as f:
            content = f.read()
        
        content = content.replace('MYSQL_HOST=localhost', f'MYSQL_HOST={host}')
        content = content.replace('MYSQL_USER=root', f'MYSQL_USER={user}')
        content = content.replace('MYSQL_PASSWORD=your_mysql_password', f'MYSQL_PASSWORD={password}')
        
        with open('.env', 'w') as f:
            f.write(content)
        
        print("✅ .env file updated with MySQL credentials")
        
    except Exception as e:
        print(f"⚠️  Failed to update .env file: {e}")

def setup_database_tables():
    """Run the database setup script"""
    print("🗄️  Setting up database tables...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        # Import after loading environment
        from models import Database
        
        db = Database()
        connection = db.get_connection()
        
        if not connection:
            print("❌ Failed to connect to database")
            return False
        
        cursor = connection.cursor()
        
        # Read and execute the SQL setup script
        with open('database_setup.sql', 'r') as f:
            sql_commands = f.read().split(';')
        
        for command in sql_commands:
            command = command.strip()
            if command:
                cursor.execute(command)
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print("✅ Database tables created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def validate_openai_key():
    """Validate OpenAI API key"""
    print("🤖 Please enter your OpenAI API key:")
    api_key = input("OpenAI API Key: ").strip()
    
    if not api_key or not api_key.startswith('sk-'):
        print("⚠️  Invalid OpenAI API key format")
        return False
    
    # Update .env file
    try:
        with open('.env', 'r') as f:
            content = f.read()
        
        content = content.replace('OPENAI_API_KEY=your_openai_api_key_here', f'OPENAI_API_KEY={api_key}')
        
        with open('.env', 'w') as f:
            f.write(content)
        
        print("✅ OpenAI API key saved")
        return True
        
    except Exception as e:
        print(f"❌ Failed to save API key: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Recipe Recommender Backend Setup")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Install requirements
    if not install_requirements():
        return False
    
    # Create .env file
    if not create_env_file():
        return False
    
    # Test MySQL connection
    if not test_mysql_connection():
        print("⚠️  Please install and configure MySQL, then run setup again")
        return False
    
    # Validate OpenAI key
    if not validate_openai_key():
        print("⚠️  Please get an OpenAI API key from https://platform.openai.com/")
        return False
    
    # Setup database tables
    if not setup_database_tables():
        return False
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Run: python app_improved.py")
    print("2. Open your browser to: http://localhost:5000")
    print("3. The frontend should connect to: http://localhost:5000/api")
    print("\n🔧 API Endpoints available:")
    print("- POST /api/register - User registration")
    print("- POST /api/login - User login")
    print("- POST /api/recipes/search - Search recipes by ingredients")
    print("- GET/POST/DELETE /api/ingredients - Manage user ingredients")
    print("- GET/POST /api/favorites - Manage favorite recipes")
    print("- GET /api/history - Get search history")
    print("- GET /api/profile - Get user profile")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Setup failed. Please check the errors above and try again.")
        sys.exit(1)
    else:
        print("\n✨ Ready to start cooking with AI! 🍳")