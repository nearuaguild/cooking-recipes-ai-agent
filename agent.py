from typing import List
from nearai.agents.environment import Environment
import json
import os
from formatters import MarkdownRecipeFormatter, RecipeFormatter
from recipes import SpoonacularRecipeProvider, RecipeProvider
import logging


class Agent:
    def __init__(
        self, client: Environment, provider: RecipeProvider, formatter: RecipeFormatter
    ):
        self.client = client
        self.recipe_provider = provider
        self.formatter = formatter

    @property
    def system_prompt(self) -> dict[str, str]:
        return {
            "role": "system",
            "content": """You are an AI assistant for a cooking recipes application. Your task is to extract as much specific information as possible from the user's natural language query and structure it into a JSON object. The JSON object should include:

                    "include_ingredients": A list of ingredients that should/must be used in the recipes.
                    "exclude_ingredients": A list of ingredients or ingredient types that the recipes must not contain.
                    "include_cuisines": A list of cuisine(s) (e.g., Italian, Indian, Japanese, American, etc.) that should/must be used in the recipes.
                    "exclude_cuisines": A list of cuisine(s) (e.g., Italian, Indian, Japanese, American, etc.) that the recipes must not use.
                    "query": Analyze the user's natural language request and classify it into a specific category (e.g. "burger", "pasta", "cookies", "salad", etc.). This field should reflect the type of meal the user is requesting rather than copying their words. If unclear, use the most likely category.
                    Only include fields mentioned by the user. If a field is not mentioned, leave it as an empty list.
                
                    Your response is just a valid JSON object and no other text.
                    If a user asks about your abilities, capabilities, or functionality, respond with a structured JSON object containing a single key, "message". This key should include a concise and friendly description of your skill which is to provide a user with a list of personalized recipes to cook at home, tailored to their preferences and requirements.""",
        }

    def parse_user_message(self, message: dict[str, str]) -> dict[str, str | List[str]]:
        completion = self.client.completion([self.system_prompt, message])

        self.client.add_agent_log(completion)

        return json.loads(completion)

    def parse_user_message_with_retries(
        self, message: dict[str, str], attempts: int = 3
    ) -> dict[str, str | List[str]]:
        for attempt in range(3):
            try:
                self.client.add_agent_log(
                    f"Attempt #{attempt + 1} to parse user message", level=logging.DEBUG
                )
                return self.parse_user_message(message)
            except json.decoder.JSONDecodeError as error:
                if attempt < attempts - 1:
                    continue
                else:
                    raise error
            # any unexpected error must be raised without retries
            except Exception as error:
                raise error

    def __run(self, user_message: dict[str, str]):
        parsed_params = self.parse_user_message_with_retries(user_message, attempts=3)

        self.client.add_agent_log(
            f"Parsed user's preferences: {str(parsed_params)}", level=logging.DEBUG
        )

        message = parsed_params.get("message")
        if isinstance(message, str):
            return self.client.add_reply(message)

        self.client.add_reply("Preparing recipes to match your taste")

        recipes = self.recipe_provider.fetch_recipes(
            query=parsed_params.get("query", ""),
            include_ingredients=parsed_params.get("include_ingredients", []),
            exclude_ingredients=parsed_params.get("exclude_ingredients", []),
            include_cuisines=parsed_params.get("include_cuisines", []),
            exclude_cuisines=parsed_params.get("exclude_cuisines", []),
            max_amount=5,
        )

        self.client.add_agent_log(
            f"Fetched {len(recipes)} recipes: {[str(recipe) for recipe in recipes]}"
        )

        if len(recipes) == 0:
            return self.client.add_reply(
                "Unfortunately, couldn't find any recipes matching your request. Please consider being more specific next time!"
            )

        self.client.add_reply(f"Found {len(recipes)} recipes for you")

        for recipe in recipes:
            text = self.formatter.transform_to_text(recipe)
            self.client.add_reply(text)

    def run(self, user_message: dict[str, str]):
        try:
            self.__run(user_message)
        except json.decoder.JSONDecodeError as error:
            self.client.add_agent_log(str(error), level=logging.ERROR)
            self.client.add_reply("Please try again")
        except Exception as error:
            self.client.add_agent_log(str(error), level=logging.ERROR)
            self.client.add_reply(
                "Something went wrong, please be patient until developer fixes it"
            )


def main(client: Environment):
    message = client.get_last_message()

    if message is None or message["role"] != "user":
        return client.request_user_input()

    api_key = os.environ.get("SPOONACULAR_API_KEY", None)

    if api_key is None:
        client.add_agent_log("Env variable SPOONACULAR_API_KEY is missing")
        return client.add_reply(
            "Environment configuration isn't complete, please be patient until the developer fixes it"
        )

    provider = SpoonacularRecipeProvider(api_key)
    formatter = MarkdownRecipeFormatter()
    agent = Agent(client, provider, formatter)
    agent.run(message)


main(env)
