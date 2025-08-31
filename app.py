# app.py
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from mysql.connector import Error
import openai
import os
from datetime import datetime, timedelta
import jwt
from functools import wraps
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'  # Change this in production
CORS(app)

# Configuration
MYSQL_CONFIG = {
    'host': 'localhost',
    'database': 'recipe_recommender',
    'user': 'root',
    'password': 'your_mysql_password'  # Change this
}

# OpenAI Configuration
openai.api_key = 'your-openai-api-key'  # Change this

# Database connection
def get_db_connection():
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        return connection
    except Error as e:
        print(f"Database connection error: {e}")
        return None

# JWT Token decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user_id = data['user_id']
        except:
            return jsonify({'message': 'Token is invalid'}), 401
        
        return f(current_user_id, *args, **kwargs)
    
    return decorated

# Database initialization
def init_database():
    """Initialize database tables"""
    connection = get_db_connection()
    if not connection:
        return False
    
    cursor = connection.cursor()
    
    try:
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create user_ingredients table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_ingredients (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                ingredient VARCHAR(100) NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Create recipes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recipes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                ingredients TEXT,
                instructions TEXT,
                cook_time VARCHAR(50),
                difficulty VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create user_favorites table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_favorites (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                recipe_id INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
            )
        """)
        
        # Create search_history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                ingredients TEXT,
                recipes_found INT,
                search_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        connection.commit()
        print("Database tables created successfully")
        return True
        
    except Error as e:
        print(f"Error creating tables: {e}")
        return False
    
    finally:
        cursor.close()
        connection.close()

# Authentication Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validate input
    if not data or not data.get('name') or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Name, email and password are required'}), 400
    
    # Validate email format
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, data['email']):
        return jsonify({'error': 'Invalid email format'}), 400
    
    # Validate password strength
    if len(data['password']) < 6:
        return jsonify({'error': 'Password must be at least 6 characters long'}), 400
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = connection.cursor()
    
    try:
        # Check if user already exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (data['email'],))
        if cursor.fetchone():
            return jsonify({'error': 'Email already registered'}), 409
        
        # Hash password and create user
        password_hash = generate_password_hash(data['password'])
        cursor.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)",
            (data['name'], data['email'], password_hash)
        )
        connection.commit()
        
        # Get user ID
        user_id = cursor.lastrowid
        
        # Generate JWT token
        token = jwt.encode({
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(days=7)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'message': 'User registered successfully',
            'token': token,
            'user': {
                'id': user_id,
                'name': data['name'],
                'email': data['email']
            }
        }), 201
        
    except Error as e:
        connection.rollback()
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500
    
    finally:
        cursor.close()
        connection.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = connection.cursor()
    
    try:
        cursor.execute(
            "SELECT id, name, email, password_hash FROM users WHERE email = %s",
            (data['email'],)
        )
        user = cursor.fetchone()
        
        if not user or not check_password_hash(user[3], data['password']):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Generate JWT token
        token = jwt.encode({
            'user_id': user[0],
            'exp': datetime.utcnow() + timedelta(days=7)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': user[0],
                'name': user[1],
                'email': user[2]
            }
        }), 200
        
    except Error as e:
        return jsonify({'error': f'Login failed: {str(e)}'}), 500
    
    finally:
        cursor.close()
        connection.close()

# Recipe Routes
@app.route('/api/recipes/search', methods=['POST'])
@token_required
def search_recipes(current_user_id):
    data = request.get_json()
    ingredients = data.get('ingredients', '')
    
    if not ingredients:
        return jsonify({'error': 'Ingredients are required'}), 400
    
    try:
        # Call OpenAI API for recipe suggestions
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful cooking assistant. Suggest 3 simple recipes using the given ingredients. Return only a JSON array with recipe objects containing: name, description, ingredients (array), instructions (array), cook_time, and difficulty."
                },
                {
                    "role": "user",
                    "content": f"Suggest 3 simple recipes with these ingredients: {ingredients}"
                }
            ],
            max_tokens=1500,
            temperature=0.7
        )
        
        # Parse OpenAI response
        recipes_text = response.choices[0].message.content
        
        # Store recipes in database and return
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Save search history
        cursor.execute(
            "INSERT INTO search_history (user_id, ingredients, recipes_found) VALUES (%s, %s, %s)",
            (current_user_id, ingredients, 3)
        )
        
        # For now, return sample recipes (you can parse OpenAI response as JSON)
        sample_recipes = [
            {
                "id": 1,
                "name": "Chicken Tomato Curry",
                "description": "A delicious and simple curry with tender chicken and fresh tomatoes",
                "ingredients": ["chicken", "tomatoes", "onions", "garlic", "spices"],
                "instructions": ["Heat oil in pan", "Add onions and garlic", "Add chicken and cook", "Add tomatoes and spices", "Simmer for 20 minutes"],
                "cook_time": "30 min",
                "difficulty": "Easy"
            },
            {
                "id": 2,
                "name": "Tomato Chicken Stir Fry",
                "description": "Quick and healthy stir fry with fresh vegetables",
                "ingredients": ["chicken", "tomatoes", "bell peppers", "soy sauce"],
                "instructions": ["Cut chicken into strips", "Heat wok", "Stir fry chicken", "Add vegetables", "Season and serve"],
                "cook_time": "20 min",
                "difficulty": "Easy"
            },
            {
                "id": 3,
                "name": "Mediterranean Chicken Bowl",
                "description": "Fresh bowl with grilled chicken and Mediterranean flavors",
                "ingredients": ["chicken", "tomatoes", "cucumber", "olive oil", "herbs"],
                "instructions": ["Grill chicken", "Chop vegetables", "Mix dressing", "Assemble bowl", "Serve fresh"],
                "cook_time": "25 min",
                "difficulty": "Medium"
            }
        ]
        
        connection.commit()
        connection.close()
        
        return jsonify({
            'recipes': sample_recipes,
            'total': len(sample_recipes),
            'ingredients_used': ingredients
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Recipe search failed: {str(e)}'}), 500

# Ingredients Routes
@app.route('/api/ingredients', methods=['GET'])
@token_required
def get_user_ingredients(current_user_id):
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = connection.cursor()
    
    try:
        cursor.execute(
            "SELECT ingredient FROM user_ingredients WHERE user_id = %s ORDER BY added_at DESC",
            (current_user_id,)
        )
        ingredients = [row[0] for row in cursor.fetchall()]
        
        return jsonify({'ingredients': ingredients}), 200
        
    except Error as e:
        return jsonify({'error': f'Failed to fetch ingredients: {str(e)}'}), 500
    
    finally:
        cursor.close()
        connection.close()

@app.route('/api/ingredients', methods=['POST'])
@token_required
def add_ingredient(current_user_id):
    data = request.get_json()
    ingredient = data.get('ingredient', '').strip().lower()
    
    if not ingredient:
        return jsonify({'error': 'Ingredient name is required'}), 400
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = connection.cursor()
    
    try:
        # Check if ingredient already exists for user
        cursor.execute(
            "SELECT id FROM user_ingredients WHERE user_id = %s AND ingredient = %s",
            (current_user_id, ingredient)
        )
        
        if cursor.fetchone():
            return jsonify({'error': 'Ingredient already added'}), 409
        
        # Add ingredient
        cursor.execute(
            "INSERT INTO user_ingredients (user_id, ingredient) VALUES (%s, %s)",
            (current_user_id, ingredient)
        )
        connection.commit()
        
        return jsonify({
            'message': 'Ingredient added successfully',
            'ingredient': ingredient
        }), 201
        
    except Error as e:
        connection.rollback()
        return jsonify({'error': f'Failed to add ingredient: {str(e)}'}), 500
    
    finally:
        cursor.close()
        connection.close()

@app.route('/api/ingredients/<ingredient>', methods=['DELETE'])
@token_required
def remove_ingredient(current_user_id, ingredient):
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = connection.cursor()
    
    try:
        cursor.execute(
            "DELETE FROM user_ingredients WHERE user_id = %s AND ingredient = %s",
            (current_user_id, ingredient.lower())
        )
        connection.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Ingredient not found'}), 404
        
        return jsonify({'message': 'Ingredient removed successfully'}), 200
        
    except Error as e:
        connection.rollback()
        return jsonify({'error': f'Failed to remove ingredient: {str(e)}'}), 500
    
    finally:
        cursor.close()
        connection.close()

# Favorites Routes
@app.route('/api/favorites', methods=['GET'])
@token_required
def get_favorites(current_user_id):
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            SELECT r.id, r.name, r.description, r.cook_time, r.difficulty
            FROM recipes r
            JOIN user_favorites uf ON r.id = uf.recipe_id
            WHERE uf.user_id = %s
            ORDER BY uf.created_at DESC
        """, (current_user_id,))
        
        favorites = []
        for row in cursor.fetchall():
            favorites.append({
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'cook_time': row[3],
                'difficulty': row[4]
            })
        
        return jsonify({'favorites': favorites}), 200
        
    except Error as e:
        return jsonify({'error': f'Failed to fetch favorites: {str(e)}'}), 500
    
    finally:
        cursor.close()
        connection.close()

@app.route('/api/favorites', methods=['POST'])
@token_required
def add_favorite(current_user_id):
    data = request.get_json()
    recipe_data = data.get('recipe', {})
    
    if not recipe_data:
        return jsonify({'error': 'Recipe data is required'}), 400
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = connection.cursor()
    
    try:
        # First, insert or get recipe
        cursor.execute(
            "SELECT id FROM recipes WHERE name = %s",
            (recipe_data['name'],)
        )
        recipe = cursor.fetchone()
        
        if recipe:
            recipe_id = recipe[0]
        else:
            # Insert new recipe
            cursor.execute("""
                INSERT INTO recipes (name, description, ingredients, instructions, cook_time, difficulty)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                recipe_data['name'],
                recipe_data.get('description', ''),
                ', '.join(recipe_data.get('ingredients', [])),
                '\n'.join(recipe_data.get('instructions', [])),
                recipe_data.get('cook_time', ''),
                recipe_data.get('difficulty', 'Medium')
            ))
            recipe_id = cursor.lastrowid
        
        # Check if already favorited
        cursor.execute(
            "SELECT id FROM user_favorites WHERE user_id = %s AND recipe_id = %s",
            (current_user_id, recipe_id)
        )
        
        if cursor.fetchone():
            return jsonify({'error': 'Recipe already in favorites'}), 409
        
        # Add to favorites
        cursor.execute(
            "INSERT INTO user_favorites (user_id, recipe_id) VALUES (%s, %s)",
            (current_user_id, recipe_id)
        )
        connection.commit()
        
        return jsonify({'message': 'Recipe added to favorites'}), 201
        
    except Error as e:
        connection.rollback()
        return jsonify({'error': f'Failed to add favorite: {str(e)}'}), 500
    
    finally:
        cursor.close()
        connection.close()

# History Routes
@app.route('/api/history', methods=['GET'])
@token_required
def get_search_history(current_user_id):
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            SELECT ingredients, recipes_found, search_time
            FROM search_history
            WHERE user_id = %s
            ORDER BY search_time DESC
            LIMIT 20
        """, (current_user_id,))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'ingredients': row[0],
                'recipes_found': row[1],
                'search_time': row[2].isoformat()
            })
        
        return jsonify({'history': history}), 200
        
    except Error as e:
        return jsonify({'error': f'Failed to fetch history: {str(e)}'}), 500
    
    finally:
        cursor.close()
        connection.close()

# User Profile Routes
@app.route('/api/profile', methods=['GET'])
@token_required
def get_profile(current_user_id):
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = connection.cursor()
    
    try:
        cursor.execute(
            "SELECT id, name, email, created_at FROM users WHERE id = %s",
            (current_user_id,)
        )
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': {
                'id': user[0],
                'name': user[1],
                'email': user[2],
                'created_at': user[3].isoformat()
            }
        }), 200
        
    except Error as e:
        return jsonify({'error': f'Failed to fetch profile: {str(e)}'}), 500
    
    finally:
        cursor.close()
        connection.close()

# OpenAI Recipe Generation Function
def generate_recipe_suggestions(ingredients):
    """Generate recipe suggestions using OpenAI API"""
    try:
        prompt = f"""
        Create 3 simple and practical recipes using these ingredients: {ingredients}
        
        For each recipe, provide:
        - Name (creative but realistic)
        - Brief description (1-2 sentences)
        - Cooking time
        - Difficulty level (Easy/Medium/Hard)
        - Step-by-step instructions (keep it simple)
        
        Focus on recipes that are:
        - Easy to follow
        - Use common cooking methods
        - Don't require too many additional ingredients
        - Are nutritious and delicious
        
        Return the response as a JSON array.
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful cooking assistant that creates practical, easy-to-follow recipes."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return None

# Health check route
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    }), 200

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Initialize database on startup
    print("Initializing database...")
    if init_database():
        print("Database initialized successfully")
    else:
        print("Database initialization failed")
    
    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5000)