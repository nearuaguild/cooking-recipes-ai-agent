from abc import abstractmethod

from recipes import Recipe


class RecipeFormatter:
    @abstractmethod
    def transform_to_text(
        self,
        recipe: Recipe,
    ) -> str:
        pass


class MarkdownRecipeFormatter(RecipeFormatter):
    def transform_to_text(self, recipe):
        bulletpoints = [
            f"| {ingredient.title} | ![{ingredient.title}]({ingredient.image}) |"
            for ingredient in recipe.ingredients
        ]
        ingredient_bulletpoints = "\n".join(bulletpoints)
        ingredient_table = f"""
| Ingredient | Image |
|------------|-------|
{ingredient_bulletpoints}
"""

        steps = [
            f"{idx + 1}. {instruction.step}"
            for idx, instruction in enumerate(recipe.instructions)
        ]
        instruction_steps = "\n".join(steps)

        return f"""
### {recipe.title}

Likes: {recipe.likes}

![Recipe Image]({recipe.image})

##### Ingredients
{ingredient_table}

##### Steps
{instruction_steps}
"""
