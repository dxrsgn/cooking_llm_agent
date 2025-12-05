import re
from src.api_handler.datamodels import Recipe, IngredientRequirement


def map_mealdb_meal_to_recipe(meal: dict, max_ingredients: int = 20) -> Recipe:
    ingredients = []

    for i in range(1, max_ingredients+1):
        name = meal.get(f"strIngredient{i}")
        measure = meal.get(f"strMeasure{i}")

        if name and name.strip():
            ingredients.append(
                IngredientRequirement(
                    name=name.strip(),
                    amount=measure.strip() if measure else None,
                )
            )

    return Recipe(
        id=meal["idMeal"],
        title=meal["strMeal"],
        ingredients=ingredients,
        instructions=meal.get("strInstructions"),
        source_url=meal.get("strSource"),
    )


def normalize_ingredient_name(text: str) -> list[str]:
    if not text:
        return []

    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)

    def singularize(word: str) -> str:
        if word.endswith("ies"):
            return word[:-3] + "y"
        if word.endswith("es"):
            return word[:-2]
        if word.endswith("s") and len(word) > 3:
            return word[:-1]
        return word

    return [singularize(w) for w in text.split()]


def recipe_has_excluded_ingredient(recipe: Recipe, excluded: set[str]) -> bool:
    for ing in recipe.ingredients:
        tokens = normalize_ingredient_name(ing.name)
        if any(ex in tokens for ex in excluded):
            return True
    return False


def count_include_matches(recipe: Recipe, include: set[str]) -> int:
    matched = set()

    for ing in recipe.ingredients:
        tokens = normalize_ingredient_name(ing.name)
        for inc in include:
            if inc in tokens:
                matched.add(inc)

    return len(matched)


def recipe_has_anchor(recipe: Recipe, anchor: str) -> bool:
    for ing in recipe.ingredients:
        tokens = normalize_ingredient_name(ing.name)
        if anchor in tokens:
            return True
    return False
