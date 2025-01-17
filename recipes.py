from abc import abstractmethod
import requests
from typing import List


class RecipeIngredient:
    def __init__(self, title: str, image: str):
        self.title = title
        self.image = image

    def __str__(self):
        json = {
            "title": self.title,
            "image": self.image,
        }
        return str(json)


class RecipeInstruction:
    def __init__(self, step: str):
        self.step = step

    def __str__(self):
        return self.step


class Recipe:
    def __init__(
        self,
        title: str,
        likes: int,
        image: str,
        ingredients: List[RecipeIngredient],
        instructions: List[RecipeInstruction],
    ):
        self.title = title
        self.likes = likes
        self.image = image
        self.ingredients = ingredients
        self.instructions = instructions

    def __str__(self):
        json = {
            "title": self.title,
            "likes": self.likes,
            "image": self.image,
            "ingredients": [str(ingredient) for ingredient in self.ingredients],
            "instructions": [str(instruction) for instruction in self.instructions],
        }
        return str(json)


class RecipeProvider:
    @abstractmethod
    def fetch_recipes(
        self,
        query: str,
        include_cuisines: List = [],
        exclude_cuisines: List = [],
        include_ingredients: List = [],
        exclude_ingredients: List = [],
        max_amount: int = 5,
    ) -> List[Recipe]:
        pass


class SpoonacularRecipeProvider(RecipeProvider):
    def __init__(self, apiKey: str):
        self.API_URL = "https://api.spoonacular.com/recipes/complexSearch"
        self.API_KEY = apiKey

    def fetch_recipes(
        self,
        query: str,
        include_cuisines: List = [],
        exclude_cuisines: List = [],
        include_ingredients: List = [],
        exclude_ingredients: List = [],
        max_amount: int = 5,
    ):
        params = {
            "query": query,
            "cuisine": ",".join(include_cuisines),
            "excludeCuisine": ",".join(exclude_cuisines),
            "includeIngredients": ",".join(include_ingredients),
            "excludeIngredients": ",".join(exclude_ingredients),
            "number": max_amount,
            "apiKey": self.API_KEY,
            "instructionsRequired": "true",
            "addRecipeInformation": "true",
            "addRecipeNutrition": "false",
            "fillIngredients": "true",
            "ignorePantry": "true",
            "sort": "calories",
            "sortDirection": "desc",
        }

        # Make the GET request to the Spoonacular API
        response = requests.get(self.API_URL, params=params)

        json_response: dict[str, any] = response.json()

        if response.status_code == 200:
            recipes = json_response.get("results", [])

            return [
                Recipe(
                    recipe.get("title"),
                    recipe.get("likes"),
                    recipe.get("image"),
                    [
                        RecipeIngredient(
                            ingredient.get("original"), ingredient.get("image")
                        )
                        for ingredient in recipe["missedIngredients"]
                        + recipe["usedIngredients"]
                    ],
                    [
                        RecipeInstruction(instruction.get("step"))
                        for instruction in recipe["analyzedInstructions"][0]["steps"]
                    ],
                )
                for recipe in recipes
            ]
        else:
            raise Exception(
                f'Error fetching recipes: {response.status_code} {json_response.get("message", "Unknown error")}'
            )
