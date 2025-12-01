from openai import AsyncOpenAI
from app.config import settings
import json
from typing import Dict, Any


async def generate_roadmap(goal_description: str) -> Dict[str, Any]:
    """
    Generate a structured learning roadmap from user's goal description using OpenAI.
    
    Args:
        goal_description: User's learning goal (e.g., "I want to learn Python for data science")
    
    Returns:
        Dict containing: title, category, difficulty, and roadmap with levels
    
    Raises:
        ValueError: If AI response cannot be parsed or is invalid
        Exception: If OpenAI API call fails
    """
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    prompt = f"""You are an expert learning path designer. A user wants to achieve this goal:

"{goal_description}"

Generate a structured learning roadmap in JSON format. Follow these rules:
1. Create a clear, concise title for the goal
2. Determine the category (e.g., Programming, Language, Business, Health, Art, etc.)
3. Assess difficulty level: "beginner", "intermediate", or "advanced"
4. Design an appropriate number of levels (typically 3-8 depending on complexity)
5. Each level should have 3-7 key topics to learn
6. Each topic should be an object with "name" and "completed" fields (all start as false)
7. Assign XP rewards (100-300 based on difficulty)
8. First level should always be unlocked

Return ONLY valid JSON in this exact structure:
{{
    "title": "Clean, professional goal title",
    "category": "Main category",
    "difficulty": "beginner|intermediate|advanced",
    "roadmap": {{
        "name": "Descriptive roadmap name",
        "levels": [
            {{
                "order": 1,
                "title": "Level title",
                "description": "What the user will learn in this level",
                "topics": [
                    {{"name": "Topic name 1", "completed": false}},
                    {{"name": "Topic name 2", "completed": false}},
                    {{"name": "Topic name 3", "completed": false}}
                ],
                "xp_reward": 100
            }}
        ]
    }}
}}

Make it practical, actionable, and motivating. NO markdown, NO code blocks, NO explanations, ONLY the JSON object."""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",  # Fast and cost-effective, or use "gpt-4" for higher quality
            messages=[
                {
                    "role": "system",
                    "content": "You are a learning path expert. Always respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=2000,
            temperature=0.7,
            response_format={"type": "json_object"}  # Forces JSON output
        )

        content = response.choices[0].message.content

        # Parse JSON
        try:
            roadmap_data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"AI returned invalid JSON: {str(e)}")

        # Validate required keys
        required_keys = ["title", "category", "difficulty", "roadmap"]
        missing_keys = [key for key in required_keys if key not in roadmap_data]
        if missing_keys:
            raise ValueError(f"AI response missing required keys: {missing_keys}")

        # Validate roadmap structure
        if "name" not in roadmap_data["roadmap"]:
            raise ValueError("Roadmap missing 'name' field")
        if "levels" not in roadmap_data["roadmap"]:
            raise ValueError("Roadmap missing 'levels' field")

        # Validate difficulty
        valid_difficulties = ["beginner", "intermediate", "advanced"]
        if roadmap_data["difficulty"] not in valid_difficulties:
            raise ValueError(f"Invalid difficulty '{roadmap_data['difficulty']}'. Must be one of: {valid_difficulties}")

        # Validate levels
        levels = roadmap_data["roadmap"]["levels"]
        if not levels or len(levels) == 0:
            raise ValueError("Roadmap must have at least one level")

        # Validate each level has required fields
        required_level_keys = ["order", "title", "description", "topics", "xp_reward"]
        for i, level in enumerate(levels):
            missing = [key for key in required_level_keys if key not in level]
            if missing:
                raise ValueError(f"Level {i+1} missing required keys: {missing}")

        return roadmap_data

    except ValueError:
        # Re-raise validation errors
        raise
    except Exception as e:
        # Wrap other errors
        raise Exception(f"Failed to generate roadmap: {str(e)}")
    




async def generate_quiz_for_level(level_title: str, level_topics: list) -> Dict[str, Any]:
    """
    Generate a quiz based on level topics using OpenAI.
    
    Args:
        level_title: Title of the level
        level_topics: List of topic objects with 'name' field
    
    Returns:
        Dict containing questions array with id, question, options, correct_answer
    """
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    
    # Extract topic names
    topic_names = [topic["name"] for topic in level_topics] if level_topics else []
    topics_text = ", ".join(topic_names)

    prompt = f"""You are an expert quiz creator. Create a quiz for students learning about: {level_title}

Topics covered:
{topics_text}

Generate 5 multiple choice questions to test understanding. Follow these rules:
1. Questions should cover the main topics listed above
2. Each question must have exactly 4 options (A, B, C, D)
3. Only ONE option is correct per question
4. Questions should range from basic recall to application
5. Make questions clear and unambiguous
6. Avoid trick questions

Return ONLY valid JSON in this exact structure:
{{
    "questions": [
        {{
            "id": 1,
            "question": "Clear question text?",
            "options": [
                {{"text": "First option", "value": "A"}},
                {{"text": "Second option", "value": "B"}},
                {{"text": "Third option", "value": "C"}},
                {{"text": "Fourth option", "value": "D"}}
            ],
            "correct_answer": "A"
        }}
    ]
}}

NO markdown, NO code blocks, NO explanations, ONLY the JSON object."""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a quiz generation expert. Always respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=2000,
            temperature=0.7,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content
        
        # Parse JSON
        try:
            quiz_data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"AI returned invalid JSON: {str(e)}")
        
        # Validate structure
        if "questions" not in quiz_data:
            raise ValueError("AI response missing 'questions' field")
        
        if len(quiz_data["questions"]) == 0:
            raise ValueError("AI generated no questions")
        
        # Validate each question
        required_keys = ["id", "question", "options", "correct_answer"]
        for i, q in enumerate(quiz_data["questions"]):
            missing = [key for key in required_keys if key not in q]
            if missing:
                raise ValueError(f"Question {i+1} missing required keys: {missing}")
            
            if len(q["options"]) != 4:
                raise ValueError(f"Question {i+1} must have exactly 4 options")
        
        return quiz_data
    
    except ValueError:
        raise
    except Exception as e:
        raise Exception(f"Failed to generate quiz: {str(e)}")