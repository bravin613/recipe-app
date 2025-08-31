
# ===================================================================
# services.py
import openai
import json
from config import Config

openai.api_key = Config.OPENAI_API_KEY

class RecipeService:
    @staticmethod
    def generate_recipes(ingredients):
        """Generate recipe suggestions using OpenAI API"""
        try:
            prompt = f"""
            Create exactly 3 practical recipes using these ingredients: {ingredients}
            
            Return ONLY a valid JSON array with this exact structure:
            [
                {{
                    "name": "Recipe Name",
                    "description": "Brief description",
                    "ingredients": ["ingredient1", "ingredient2"],
                    "instructions": ["step1", "step2", "step3"],
                    "cook_time": "XX min",
                    "difficulty": "Easy"
                }}
            ]
            
            Requirements:
            - Use mainly the provided ingredients
            - Keep recipes simple and practical
            - Instructions should be clear and concise
            - Difficulty should be Easy, Medium, or Hard
            - Cook time should be realistic
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a professional chef assistant. Return only valid JSON arrays for recipe suggestions."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            # Parse the JSON response
            recipes_text = response.choices[0].message.content.strip()
            
            # Clean up the response to ensure it's valid JSON
            if recipes_text.startswith('```json'):
                recipes_text = recipes_text[7:-3]
            elif recipes_text.startswith('```'):
                recipes_text = recipes_text[3:-3]
            
            recipes = json.loads(recipes_text)
            
            # Validate the response structure
            if not isinstance(recipes, list):
                raise ValueError("Response is not a list")
            
            for recipe in recipes:
                required_fields = ['name', 'description', 'ingredients', 'instructions', 'cook_time', 'difficulty']
                if not all(field in recipe for field in required_fields):
                    raise ValueError("Recipe missing required fields")
            
            return recipes
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            return RecipeService.get_fallback_recipes(ingredients)
        
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return RecipeService.get_fallback_recipes(ingredients)
    
    @staticmethod
    def get_fallback_recipes(ingredients):
        """Fallback recipes when OpenAI API fails"""
        return [
            {
                "name": f"Simple {ingredients.split(',')[0].strip()} Dish",
                "description": "A quick and easy recipe using your available ingredients",
                "ingredients": [ing.strip() for ing in ingredients.split(',')[:5]],
                "instructions": [
                    "Prepare all ingredients",
                    "Heat oil in a pan",
                    "Cook main ingredients until done",
                    "Season to taste",
                    "Serve hot"
                ],
                "cook_time": "20 min",
                "difficulty": "Easy"
            },
            {
                "name": f"Healthy {ingredients.split(',')[0].strip()} Bowl",
                "description": "A nutritious bowl combining fresh ingredients",
                "ingredients": [ing.strip() for ing in ingredients.split(',')[:4]],
                "instructions": [
                    "Prepare vegetables",
                    "Cook protein if needed",
                    "Arrange in a bowl",
                    "Add dressing",
                    "Enjoy fresh"
                ],
                "cook_time": "15 min",
                "difficulty": "Easy"
            },
            {
                "name": f"Classic {ingredients.split(',')[0].strip()} Recipe",
                "description": "A traditional preparation method",
                "ingredients": [ing.strip() for ing in ingredients.split(',')[:6]],
                "instructions": [
                    "Preheat cooking surface",
                    "Season ingredients",
                    "Cook according to preference",
                    "Let rest briefly",
                    "Serve and enjoy"
                ],
                "cook_time": "25 min",
                "difficulty": "Medium"
            }
        ]
