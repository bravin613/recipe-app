-- Database Setup for Recipe Recommender
-- Run this script in MySQL to create the database and tables

-- Create database
CREATE DATABASE IF NOT EXISTS recipe_recommender;
USE recipe_recommender;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Create user_ingredients table
CREATE TABLE IF NOT EXISTS user_ingredients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    ingredient VARCHAR(100) NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_ingredient (user_id, ingredient)
);

-- Create recipes table
CREATE TABLE IF NOT EXISTS recipes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    ingredients TEXT,
    instructions TEXT,
    cook_time VARCHAR(50),
    difficulty ENUM('Easy', 'Medium', 'Hard') DEFAULT 'Medium',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create user_favorites table
CREATE TABLE IF NOT EXISTS user_favorites (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    recipe_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_recipe (user_id, recipe_id)
);

-- Create search_history table
CREATE TABLE IF NOT EXISTS search_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    ingredients TEXT NOT NULL,
    recipes_found INT DEFAULT 0,
    search_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create indexes for better performance
CREATE INDEX idx_user_ingredients_user_id ON user_ingredients(user_id);
CREATE INDEX idx_user_favorites_user_id ON user_favorites(user_id);
CREATE INDEX idx_search_history_user_id ON search_history(user_id);
CREATE INDEX idx_recipes_difficulty ON recipes(difficulty);

-- Insert sample recipes for testing
INSERT INTO recipes (name, description, ingredients, instructions, cook_time, difficulty) VALUES
('Chicken Tomato Curry', 'A delicious and simple curry with tender chicken and fresh tomatoes', 'chicken, tomatoes, onions, garlic, ginger, curry powder, coconut milk', 'Heat oil in pan\nAdd onions and garlic\nAdd chicken and cook until golden\nAdd tomatoes and spices\nPour coconut milk and simmer for 20 minutes', '30 min', 'Easy'),

('Quick Vegetable Stir Fry', 'Fresh vegetables stir-fried with aromatic seasonings', 'mixed vegetables, soy sauce, garlic, ginger, sesame oil', 'Heat oil in wok\nAdd garlic and ginger\nAdd vegetables and stir fry\nSeason with soy sauce\nServe hot with rice', '15 min', 'Easy'),

('Mediterranean Pasta Salad', 'Light and refreshing pasta salad with Mediterranean flavors', 'pasta, tomatoes, olives, feta cheese, olive oil, herbs', 'Cook pasta according to package instructions\nDrain and cool\nMix with chopped vegetables\nAdd dressing and cheese\nChill before serving', '20 min', 'Easy');

-- Create a view for user recipe recommendations
CREATE VIEW user_recipe_stats AS
SELECT 
    u.id as user_id,
    u.name as user_name,
    COUNT(DISTINCT ui.ingredient) as total_ingredients,
    COUNT(DISTINCT uf.recipe_id) as total_favorites,
    COUNT(DISTINCT sh.id) as total_searches
FROM users u
LEFT JOIN user_ingredients ui ON u.id = ui.user_id
LEFT JOIN user_favorites uf ON u.id = uf.user_id
LEFT JOIN search_history sh ON u.id = sh.user_id
GROUP BY u.id, u.name;