# ===================================================================
# app_improved.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from functools import wraps
import re

# Import our custom classes
from models import User, Ingredient, Recipe, Favorite, SearchHistory
from services import RecipeService
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Initialize model instances
user_model = User()
ingredient_model = Ingredient()
recipe_model = Recipe()
favorite_model = Favorite()
history_model = SearchHistory()

# JWT Token decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Authentication token is missing'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token is invalid'}), 401
        
        return f(current_user_id, *args, **kwargs)
    
    return decorated


def validate_password(password):
    return len(password) >= 6

# Authentication Routes
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Validate input
        if not data or not all(k in data for k in ['name', 'email', 'password']):
            return jsonify({'error': 'Name, email and password are required'}), 400
        
        if not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        
        if not validate_password(data['password']):
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        
        # Check if user already exists
        if user_model.email_exists(data['email']):
            return jsonify({'error': 'Email already registered'}), 409
        
        # Create user
        password_hash = generate_password_hash(data['password'])
        user_id = user_model.create_user(data['name'], data['email'], password_hash)
        
        if not user_id:
            return jsonify({'error': 'Failed to create user'}), 500
        
        # Generate JWT token
        token = jwt.encode({
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(days=Config.JWT_EXPIRATION_DAYS)
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
        
    except Exception as e:
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data or not all(k in data for k in ['email', 'password']):
            return jsonify({'error': 'Email and password are required'}), 400
        
        user = user_model.get_user_by_email(data['email'])
        
        if not user or not check_password_hash(user[3], data['password']):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Generate JWT token
        token = jwt.encode({
            'user_id': user[0],
            'exp': datetime.utcnow() + timedelta(days=Config.JWT_EXPIRATION_DAYS)
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
        
    except Exception as e:
        return jsonify({'error': f'Login failed: {str(e)}'}), 500

# Recipe Routes
@app.route('/api/recipes/search', methods=['POST'])
@token_required
def search_recipes(current_user_id):
    try:
        data = request.get_json()
        ingredients = data.get('ingredients', '').strip()
        
        if not ingredients:
            return jsonify({'error': 'Ingredients are required'}), 400
        
        # Generate recipes using OpenAI
        recipes = RecipeService.generate_recipes(ingredients)
        
        # Save search history
        history_model.add_search(current_user_id, ingredients, len(recipes))
        
        # Store recipes in database for future reference
        for recipe_data in recipes:
            recipe_model.create_recipe(
                recipe_data['name'],
                recipe_data['description'],
                ', '.join(recipe_data['ingredients']),
                '\n'.join(recipe_data['instructions']),
                recipe_data['cook_time'],
                recipe_data['difficulty']
            )
        
        return jsonify({
            'recipes': recipes,
            'total': len(recipes),
            'ingredients_used': ingredients
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Recipe search failed: {str(e)}'}), 500

# Ingredients Routes
@app.route('/api/ingredients', methods=['GET'])
@token_required
def get_ingredients(current_user_id):
    try:
        ingredients = ingredient_model.get_user_ingredients(current_user_id)
        return jsonify({'ingredients': ingredients}), 200
    except Exception as e:
        return jsonify({'error': f'Failed to fetch ingredients: {str(e)}'}), 500

@app.route('/api/ingredients', methods=['POST'])
@token_required
def add_ingredient(current_user_id):
    try:
        data = request.get_json()
        ingredient = data.get('ingredient', '').strip()
        
        if not ingredient:
            return jsonify({'error': 'Ingredient name is required'}), 400
        
        if ingredient_model.ingredient_exists(current_user_id, ingredient):
            return jsonify({'error': 'Ingredient already added'}), 409
        
        if ingredient_model.add_ingredient(current_user_id, ingredient):
            return jsonify({
                'message': 'Ingredient added successfully',
                'ingredient': ingredient.lower()
            }), 201
        else:
            return jsonify({'error': 'Failed to add ingredient'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Failed to add ingredient: {str(e)}'}), 500

@app.route('/api/ingredients/<ingredient>', methods=['DELETE'])
@token_required
def remove_ingredient(current_user_id, ingredient):
    try:
        if ingredient_model.remove_ingredient(current_user_id, ingredient):
            return jsonify({'message': 'Ingredient removed successfully'}), 200
        else:
            return jsonify({'error': 'Ingredient not found'}), 404
            
    except Exception as e:
        return jsonify({'error': f'Failed to remove ingredient: {str(e)}'}), 500

# Favorites Routes
@app.route('/api/favorites', methods=['GET'])
@token_required
def get_favorites(current_user_id):
    try:
        favorites_data = favorite_model.get_user_favorites(current_user_id)
        
        favorites = []
        if favorites_data:
            for row in favorites_data:
                favorites.append({
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'cook_time': row[3],
                    'difficulty': row[4]
                })
        
        return jsonify({'favorites': favorites}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch favorites: {str(e)}'}), 500

@app.route('/api/favorites', methods=['POST'])
@token_required
def add_favorite_recipe(current_user_id):
    try:
        data = request.get_json()
        recipe_data = data.get('recipe', {})
        
        if not recipe_data or not recipe_data.get('name'):
            return jsonify({'error': 'Recipe data is required'}), 400
        
        # Check if recipe exists, create if not
        existing_recipe = recipe_model.get_recipe_by_name(recipe_data['name'])
        
        if existing_recipe:
            recipe_id = existing_recipe[0]
        else:
            # Create new recipe
            recipe_id = recipe_model.create_recipe(
                recipe_data['name'],
                recipe_data.get('description', ''),
                ', '.join(recipe_data.get('ingredients', [])),
                '\n'.join(recipe_data.get('instructions', [])),
                recipe_data.get('cook_time', ''),
                recipe_data.get('difficulty', 'Medium')
            )
        
        if not recipe_id:
            return jsonify({'error': 'Failed to create recipe'}), 500
        
        # Check if already favorited
        if favorite_model.is_favorite(current_user_id, recipe_id):
            return jsonify({'error': 'Recipe already in favorites'}), 409
        
        # Add to favorites
        if favorite_model.add_favorite(current_user_id, recipe_id):
            return jsonify({'message': 'Recipe added to favorites'}), 201
        else:
            return jsonify({'error': 'Failed to add to favorites'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Failed to add favorite: {str(e)}'}), 500

# History Routes
@app.route('/api/history', methods=['GET'])
@token_required
def get_history(current_user_id):
    try:
        history_data = history_model.get_user_history(current_user_id)
        
        history = []
        if history_data:
            for row in history_data:
                history.append({
                    'ingredients': row[0],
                    'recipes_found': row[1],
                    'search_time': row[2].isoformat() if row[2] else None
                })
        
        return jsonify({'history': history}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch history: {str(e)}'}), 500

# User Profile Routes
@app.route('/api/profile', methods=['GET'])
@token_required
def get_profile(current_user_id):
    try:
        user_data = user_model.get_user_by_id(current_user_id)
        
        if not user_data:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': {
                'id': user_data[0],
                'name': user_data[1],
                'email': user_data[2],
                'created_at': user_data[3].isoformat() if user_data[3] else None
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch profile: {str(e)}'}), 500

# Utility Routes
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    }), 200

@app.route('/api/stats', methods=['GET'])
@token_required
def get_user_stats(current_user_id):
    try:
        ingredients = ingredient_model.get_user_ingredients(current_user_id)
        favorites = favorite_model.get_user_favorites(current_user_id)
        history = history_model.get_user_history(current_user_id, limit=5)
        
        return jsonify({
            'stats': {
                'total_ingredients': len(ingredients),
                'total_favorites': len(favorites) if favorites else 0,
                'total_searches': len(history) if history else 0,
                'recent_ingredients': ingredients[:5],
                'last_search': history[0] if history else None
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch stats: {str(e)}'}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400

# CORS headers for all responses
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

if __name__ == '__main__':
    print("Starting Recipe Recommender Backend...")
    print("Ensure you have:")
    print("1. MySQL server running")
    print("2. Created the database: recipe_recommender")
    print("3. Set environment variables in .env file")
    print("4. Installed requirements: pip install -r requirements.txt")
    
    app.run(debug=True, host='0.0.0.0', port=5000)