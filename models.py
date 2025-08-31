# models.py
import mysql.connector
from mysql.connector import Error
from config import Config

class Database:
    def __init__(self):
        self.config = {
            'host': Config.MYSQL_HOST,
            'database': Config.MYSQL_DATABASE,
            'user': Config.MYSQL_USER,
            'password': Config.MYSQL_PASSWORD,
            'autocommit': False
        }
    
    def get_connection(self):
        try:
            connection = mysql.connector.connect(**self.config)
            return connection
        except Error as e:
            print(f"Database connection error: {e}")
            return None
    
    def execute_query(self, query, params=None, fetch=False):
        connection = self.get_connection()
        if not connection:
            return None
        
        cursor = connection.cursor()
        
        try:
            cursor.execute(query, params or ())
            
            if fetch:
                if fetch == 'one':
                    result = cursor.fetchone()
                else:
                    result = cursor.fetchall()
                connection.commit()
                return result
            else:
                connection.commit()
                return cursor.lastrowid
                
        except Error as e:
            connection.rollback()
            print(f"Query execution error: {e}")
            return None
        
        finally:
            cursor.close()
            connection.close()

class User:
    def __init__(self):
        self.db = Database()
    
    def create_user(self, name, email, password_hash):
        query = "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)"
        return self.db.execute_query(query, (name, email, password_hash))
    
    def get_user_by_email(self, email):
        query = "SELECT id, name, email, password_hash FROM users WHERE email = %s"
        return self.db.execute_query(query, (email,), fetch='one')
    
    def get_user_by_id(self, user_id):
        query = "SELECT id, name, email, created_at FROM users WHERE id = %s"
        return self.db.execute_query(query, (user_id,), fetch='one')
    
    def email_exists(self, email):
        query = "SELECT id FROM users WHERE email = %s"
        result = self.db.execute_query(query, (email,), fetch='one')
        return result is not None

class Ingredient:
    def __init__(self):
        self.db = Database()
    
    def add_ingredient(self, user_id, ingredient):
        query = "INSERT INTO user_ingredients (user_id, ingredient) VALUES (%s, %s)"
        return self.db.execute_query(query, (user_id, ingredient.lower()))
    
    def get_user_ingredients(self, user_id):
        query = "SELECT ingredient FROM user_ingredients WHERE user_id = %s ORDER BY added_at DESC"
        results = self.db.execute_query(query, (user_id,), fetch='all')
        return [row[0] for row in results] if results else []
    
    def remove_ingredient(self, user_id, ingredient):
        query = "DELETE FROM user_ingredients WHERE user_id = %s AND ingredient = %s"
        return self.db.execute_query(query, (user_id, ingredient.lower()))
    
    def ingredient_exists(self, user_id, ingredient):
        query = "SELECT id FROM user_ingredients WHERE user_id = %s AND ingredient = %s"
        result = self.db.execute_query(query, (user_id, ingredient.lower()), fetch='one')
        return result is not None

class Recipe:
    def __init__(self):
        self.db = Database()
    
    def create_recipe(self, name, description, ingredients, instructions, cook_time, difficulty):
        query = """
        INSERT INTO recipes (name, description, ingredients, instructions, cook_time, difficulty)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        return self.db.execute_query(query, (name, description, ingredients, instructions, cook_time, difficulty))
    
    def get_recipe_by_name(self, name):
        query = "SELECT id FROM recipes WHERE name = %s"
        return self.db.execute_query(query, (name,), fetch='one')

class Favorite:
    def __init__(self):
        self.db = Database()
    
    def add_favorite(self, user_id, recipe_id):
        query = "INSERT INTO user_favorites (user_id, recipe_id) VALUES (%s, %s)"
        return self.db.execute_query(query, (user_id, recipe_id))
    
    def get_user_favorites(self, user_id):
        query = """
        SELECT r.id, r.name, r.description, r.cook_time, r.difficulty
        FROM recipes r
        JOIN user_favorites uf ON r.id = uf.recipe_id
        WHERE uf.user_id = %s
        ORDER BY uf.created_at DESC
        """
        return self.db.execute_query(query, (user_id,), fetch='all')
    
    def is_favorite(self, user_id, recipe_id):
        query = "SELECT id FROM user_favorites WHERE user_id = %s AND recipe_id = %s"
        result = self.db.execute_query(query, (user_id, recipe_id), fetch='one')
        return result is not None

class SearchHistory:
    def __init__(self):
        self.db = Database()
    
    def add_search(self, user_id, ingredients, recipes_found):
        query = "INSERT INTO search_history (user_id, ingredients, recipes_found) VALUES (%s, %s, %s)"
        return self.db.execute_query(query, (user_id, ingredients, recipes_found))
    
    def get_user_history(self, user_id, limit=20):
        query = """
        SELECT ingredients, recipes_found, search_time
        FROM search_history
        WHERE user_id = %s
        ORDER BY search_time DESC
        LIMIT %s
        """
        return self.db.execute_query(query, (user_id, limit), fetch='all')
