import json
from typing import List, Dict, Any, Optional
from src.services.llm_service import LLMService
from src.core.models import Quiz, Question, Answer, QuizResult

class QuizGenerator:
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    async def generate_quiz(
        self,
        content: str,
        quiz_type: str,
        num_questions: int,
        topic: Optional[str] = None,
        difficulty: Optional[str] = None,
        language: str = "en"
    ) -> Dict[str, Any]:
        
        prompt = self._build_quiz_generation_prompt(content, quiz_type, num_questions, topic, difficulty, language)
        
        try:
            llm_response = await self.llm_service.generate_response(prompt)
            print(f"LLM Raw Response: {llm_response}") # Debugging LLM raw response
            parsed_quiz_data = self._parse_llm_response(llm_response, quiz_type)
            
            # Enforce num_questions constraint after parsing
            # Enforce num_questions constraint after parsing
            if len(parsed_quiz_data) > num_questions:
                parsed_quiz_data = parsed_quiz_data[:num_questions]
            
            # Retry mechanism to generate more questions if needed
            retries = 0
            max_retries = 2
            while len(parsed_quiz_data) < num_questions and retries < max_retries:
                retries += 1
                remaining_questions_to_generate = num_questions - len(parsed_quiz_data)
                print(f"Attempting to generate {remaining_questions_to_generate} more questions (Retry {retries}/{max_retries})...")
                
                # Build a new prompt for the remaining questions
                retry_prompt = self._build_quiz_generation_prompt(
                    content, quiz_type, remaining_questions_to_generate, topic, difficulty, language
                )
                
                try:
                    retry_llm_response = await self.llm_service.generate_response(retry_prompt)
                    print(f"LLM Raw Response (Retry {retries}): {retry_llm_response}")
                    new_parsed_data = self._parse_llm_response(retry_llm_response, quiz_type)
                    
                    # Add only unique questions from the retry
                    for q in new_parsed_data:
                        if len(parsed_quiz_data) < num_questions and q not in parsed_quiz_data:
                            parsed_quiz_data.append(q)
                except Exception as retry_e:
                    print(f"Error during quiz generation retry {retries}: {retry_e}")
            
            if len(parsed_quiz_data) < num_questions:
                print(f"Warning: After {max_retries} retries, LLM generated {len(parsed_quiz_data)} questions, but {num_questions} were requested.")
            
            return {"questions": parsed_quiz_data}
        except ValueError as e:
            print(f"Error parsing LLM response for quiz generation: {e}")
            # If parsing fails, return an empty list of questions or a specific error message
            return {"questions": [], "error": f"Failed to generate quiz due to LLM response parsing error: {e}"}
        except Exception as e:
            print(f"Error generating quiz with LLM: {e}")
            # Re-raise other unexpected exceptions
            raise

    def _build_quiz_generation_prompt(
        self,
        content: str,
        quiz_type: str,
        num_questions: int,
        topic: Optional[str],
        difficulty: Optional[str],
        language: str
    ) -> str:
        
        topic_clause = f"on the topic of '{topic}'" if topic else ""
        difficulty_clause = f"of '{difficulty}' difficulty" if difficulty else ""
        language_instruction = ""
        if language == "de":
            language_instruction = "The questions and answers MUST be in German."
        elif language == "sk":
            language_instruction = "The questions and answers MUST be in Slovak."
        elif language == "en":
            language_instruction = "The questions and answers MUST be in English."

        base_prompt = f"""
You are an expert quiz generator. Your task is to create a quiz with exactly {num_questions} questions of type '{quiz_type}' {topic_clause} {difficulty_clause} based STRICTLY ONLY on the provided content.
{language_instruction}

**CRITICAL INSTRUCTIONS:**
1.  Generate EXACTLY {num_questions} questions. No more, no less.
2.  The quiz MUST be of type '{quiz_type}'. Do NOT include questions of other types.
3.  Each question MUST strictly adhere to the provided `topic` and the `Provided Content`.
4.  Each question MUST include the `question_text`, `question_type`, and `correct_answer`.
5.  For 'multiple_choice' questions, include an `options` list with 4 distinct choices, one of which is the `correct_answer`.
6.  For 'true_false' questions, the `options` list MUST be `["True", "False"]`.
7.  For 'fill_in_the_blank' questions, indicate the blank with `[BLANK]` in the `question_text` and provide the missing word/phrase as the `correct_answer`. Do NOT include options for fill-in-the-blank.
8.  The output MUST be a JSON array of question objects. Do NOT include any other text or formatting outside the JSON.
9.  Ensure the difficulty is {difficulty} if specified.

**IMPORTANT: Adherence to Quiz Type**
- If `quiz_type` is 'true_false', absolutely DO NOT generate 'multiple_choice', 'fill_in_the_blank', or 'short_answer' questions.
- If `quiz_type` is 'multiple_choice', absolutely DO NOT generate 'true_false', 'fill_in_the_blank', or 'short_answer' questions.
- If `quiz_type` is 'fill_in_the_blank', absolutely DO NOT generate 'multiple_choice', 'true_false', or 'short_answer' questions.
- If `quiz_type` is 'short_answer', absolutely DO NOT generate 'multiple_choice', 'true_false', or 'fill_in_the_blank' questions.

**Example JSON Structure for Multiple Choice:**
```json
[
    {{
        "question_text": "What is the capital of France?",
        "question_type": "multiple_choice",
        "options": ["Berlin", "Madrid", "Paris", "Rome"],
        "correct_answer": "Paris"
    }}
]
```

**Example JSON Structure for True/False:**
```json
[
    {{
        "question_text": "The Earth is flat.",
        "question_type": "true_false",
        "options": ["True", "False"],
        "correct_answer": "False"
    }}
]
```

**Example JSON Structure for Fill-in-the-blank:**
```json
[
    {{
        "question_text": "The chemical symbol for water is [BLANK].",
        "question_type": "fill_in_the_blank",
        "correct_answer": "H2O"
    }}
]
```

**Provided Content:**
---
{content}
---

Generate the {quiz_type} quiz questions in JSON format. Your response MUST contain ONLY the JSON array and nothing else.
"""
        return base_prompt

    def _parse_llm_response(self, llm_response: str, quiz_type: str) -> List[Dict[str, Any]]:
        try:
            # Attempt to find the JSON array in the response
            # Robustly handle markdown code blocks or extraneous text.
            import re
            json_str = ""
            
            # First, try to extract JSON from a markdown code block
            json_match = re.search(r'```json\s*(\[[\s\S]*?\])\s*```', llm_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # If no markdown block, try to find a standalone JSON array
                json_match = re.search(r'(\[\s*\{[\s\S]*?\}\s*\])', llm_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
            
            if not json_str:
                raise ValueError("Could not find a JSON array in the LLM response.")
            
            # Pre-processing: Replace single quotes with double quotes, remove trailing commas
            json_str = json_str.replace("'", '"')
            json_str = re.sub(r',\s*([\]}])', r'\1', json_str)
            
            print(f"DEBUG: Extracted and cleaned JSON string (pre-parse): {json_str}")
            
            try:
                parsed_data = json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"DEBUG: Initial JSON parse failed. Attempting aggressive quote escaping. Error: {e}")
                # Aggressively escape unescaped double quotes within string values
                # This pattern looks for a double quote that is not preceded by an odd number of backslashes
                # and is not part of a key or structural element.
                # This is a heuristic and might require further refinement based on LLM output patterns.
                
                # A more robust approach for unescaped quotes within values:
                # Iterate through the string and escape quotes that are not part of JSON structure.
                # This is a simplified heuristic for common cases.
                
                # This specific regex targets unescaped quotes within string values,
                # assuming the overall structure is mostly correct.
                # It looks for a quote that is not at the start/end of a key or value,
                # and not already escaped.
                
                # This is a very difficult problem to solve with regex alone for all cases.
                # A common issue is a double quote inside a string value, e.g., "text": "He said "hello"."
                # We need to change it to: "text": "He said \"hello\"."
                
                # This regex attempts to fix unescaped double quotes within string values.
                # It looks for a pattern like "key": "value with "inner" quote" and escapes the inner quote.
                # This is a heuristic and might not catch all edge cases, but addresses common LLM output issues.
                # A more robust approach for unescaped quotes within values:
                # Iterate through the string and escape quotes that are not part of JSON structure.
                # This is a simplified heuristic for common cases.
                
                # This regex attempts to fix unescaped double quotes within string values.
                # It looks for a pattern like "key": "value with "inner" quote" and escapes the inner quote.
                # This is a heuristic and might not catch all edge cases, but addresses common LLM output issues.
                # The previous regex was too broad. Let's try a more targeted approach.
                
                # This is a very difficult problem to solve with regex alone for all cases.
                # A common issue is a double quote inside a string value, e.g., "text": "He said "hello"."
                # We need to change it to: "text": "He said \"hello\"."
                
                # Let's try to fix the specific error pattern: "text": "The term "AI" stands for..."
                # This means a double quote inside a double-quoted string.
                json_str = re.sub(r'("question_text":\s*".*?)"(.*?)"', r'\1\\"\2"', json_str, flags=re.DOTALL)
                json_str = re.sub(r'("correct_answer":\s*".*?)"(.*?)"', r'\1\\"\2"', json_str, flags=re.DOTALL)
                json_str = re.sub(r'("explanation":\s*".*?)"(.*?)"', r'\1\\"\2"', json_str, flags=re.DOTALL)
                
                # Remove any remaining invalid control characters (e.g., unescaped newlines, tabs)
                json_str = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', json_str)
                
                print(f"DEBUG: Extracted and aggressively cleaned JSON string: {json_str}")
                parsed_data = json.loads(json_str)
            
            
            # Basic validation
            if not isinstance(parsed_data, list):
                raise ValueError("LLM response is not a JSON array.")
            
            # Post-generation validation and filtering for generic questions
            filtered_data = []
            generic_question_keywords = [
                "main topic", "summarize", "main idea", "what is this document about",
                "number of sections", "number of pages", "structure of the document"
            ]

            for q in parsed_data:
                # Basic validation
                if not all(k in q for k in ["question_text", "question_type", "correct_answer"]):
                    print(f"Warning: Missing required fields in a question object: {q}. Skipping.")
                    continue
                if q["question_type"] == "multiple_choice" and "options" not in q:
                    print(f"Warning: Multiple choice question missing options: {q}. Skipping.")
                    continue
                if q["question_type"] == "true_false":
                    # Ensure options are ["True", "False"]
                    if q.get("options") != ["True", "False"]:
                        print(f"Warning: True/False question options not as expected: {q.get('options')}. Forcing to ['True', 'False'].")
                        q["options"] = ["True", "False"]
                
                # Check for generic questions
                is_generic = False
                for keyword in generic_question_keywords:
                    if keyword in q["question_text"].lower():
                        is_generic = True
                        break
                
                if is_generic:
                    print(f"Warning: Detected generic question: '{q['question_text']}'. Skipping.")
                    continue
                
                # Post-generation validation for question type adherence
                if q["question_type"] != quiz_type:
                    print(f"Warning: Question type mismatch. Expected '{quiz_type}', got '{q['question_type']}'. Skipping question: '{q['question_text']}'.")
                    continue

                filtered_data.append(q)
            
            return filtered_data
        except json.JSONDecodeError as e:
            print(f"JSON decoding error: {e}")
            print(f"Problematic LLM response: {llm_response}")
            raise ValueError(f"Failed to parse LLM response as JSON: {e}")
        except ValueError as e:
            print(f"Validation error in parsed quiz data: {e}")
            print(f"Problematic LLM response: {llm_response}")
            raise ValueError(f"Invalid quiz data structure from LLM: {e}")
        except Exception as e:
            print(f"Unexpected error parsing LLM response: {e}")
            print(f"Problematic LLM response: {llm_response}")
            raise ValueError(f"An unexpected error occurred during parsing: {e}. LLM response: {llm_response}")

    async def generate_study_suggestions(
        self,
        quiz: Quiz,
        quiz_result: QuizResult,
        user_answers: List[Answer]
    ) -> str:
        incorrect_questions = [
            (q, ua) for q in quiz.questions 
            for ua in user_answers 
            if ua.question_id == q.id and not ua.is_correct
        ]

        if not incorrect_questions:
            return "Great job! You answered all questions correctly. Keep up the excellent work!"

        # Build prompt for study suggestions
        prompt_parts = [
            "You are an AI tutor specializing in providing helpful study suggestions.",
            f"A user just completed a quiz titled '{quiz.title}' and scored {quiz_result.score} out of {quiz_result.total_questions}.",
            "They answered the following questions incorrectly. For each incorrect answer, provide a concise and actionable study suggestion. These suggestions MUST be directly related to the specific incorrect question and its correct answer, and should guide the user to review the relevant concepts from the original content.",
            "DO NOT generate new questions, general study tips, or information not directly tied to the incorrect answers. If all questions were answered correctly, return only a positive reinforcement message.",
            "Focus strictly on the core concepts related to the incorrect answers and suggest specific areas for review from the provided content.",
            "\n--- Incorrect Questions and User Answers ---"
        ]

        for q, ua in incorrect_questions:
            prompt_parts.append(f"Question: {q.question_text}")
            if q.options:
                prompt_parts.append(f"Options: {', '.join(q.options)}")
            prompt_parts.append(f"Correct Answer: {q.correct_answer}")
            prompt_parts.append(f"User's Answer: {ua.user_answer}")
            prompt_parts.append("---")

        prompt_parts.append("\n--- Original Quiz Content ---")
        # Assuming quiz.asset.content holds the original content. This might need adjustment
        # if quizzes can be generated from multiple assets or if content is not directly linked.
        # For now, let's assume a single asset or that the content is passed in another way if needed.
        # If quiz.asset is None, we might need to fetch content from associated sources.
        # For simplicity, let's assume quiz.asset.content is available or we'll refine this later.
        if quiz.asset and quiz.asset.content:
            prompt_parts.append(quiz.asset.content)
        else:
            prompt_parts.append("Original content not directly available for this quiz.")

        prompt_parts.append("\n--- Study Suggestions ---")
        
        full_prompt = "\n".join(prompt_parts)

        try:
            suggestion_response = await self.llm_service.generate_response(full_prompt)
            return suggestion_response
        except Exception as e:
            print(f"Error generating study suggestions with LLM: {e}")
            return "Failed to generate study suggestions due to an internal error."
