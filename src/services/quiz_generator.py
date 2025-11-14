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
        
        # Truncate content to prevent exceeding LLM context window
        # Using a larger limit for robust file analysis
        max_content_length = 20000 
        truncated_content = content[:max_content_length] if len(content) > max_content_length else content

        try:
            # Call the LLMService's quiz generation method directly
            # This method now handles provider-specific prompt building and returns raw LLM response
            llm_raw_response = await self.llm_service.generate_quiz_questions(
                content=truncated_content,
                quiz_type=quiz_type,
                num_questions=num_questions,
                topic=topic,
                difficulty=difficulty,
                language=language
            )

            if "error" in llm_raw_response:
                return {"questions": [], "error": llm_raw_response["error"]}
            
            raw_response_text = llm_raw_response.get("raw_response_text", "")
            if not raw_response_text:
                raise ValueError("LLMService did not return raw_response_text for quiz generation.")

            print(f"LLM Raw Response: {raw_response_text}") # Debugging LLM raw response
            parsed_quiz_data = self._parse_llm_response(raw_response_text, quiz_type)
            
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
                
                # Call LLMService again for remaining questions
                retry_llm_raw_response = await self.llm_service.generate_quiz_questions(
                    content=truncated_content,
                    quiz_type=quiz_type,
                    num_questions=remaining_questions_to_generate, # Request only remaining questions
                    topic=topic,
                    difficulty=difficulty,
                    language=language
                )
                
                if "error" in retry_llm_raw_response:
                    print(f"Error during quiz generation retry {retries}: {retry_llm_raw_response['error']}")
                    break # Stop retrying if LLMService itself reports an error
                
                retry_raw_response_text = retry_llm_raw_response.get("raw_response_text", "")
                if not retry_raw_response_text:
                    print(f"Warning: LLMService did not return raw_response_text for quiz generation retry {retries}.")
                    break

                print(f"LLM Raw Response (Retry {retries}): {retry_raw_response_text}")
                new_parsed_data = self._parse_llm_response(retry_raw_response_text, quiz_type)
                
                # Add only unique questions from the retry
                for q in new_parsed_data:
                    if len(parsed_quiz_data) < num_questions and q not in parsed_quiz_data:
                        parsed_quiz_data.append(q)
            
            if len(parsed_quiz_data) < num_questions:
                print(f"Warning: After {max_retries} retries, LLM generated {len(parsed_quiz_data)} questions, but {num_questions} were requested.")
            
            return {"questions": parsed_quiz_data}
        except ValueError as e:
            print(f"Error parsing LLM response for quiz generation: {e}")
            return {"questions": [], "error": f"Failed to generate quiz due to LLM response parsing error: {e}"}
        except Exception as e:
            print(f"Error generating quiz with LLM: {e}")
            raise

    def _parse_llm_response(self, llm_response: str, quiz_type: str) -> List[Dict[str, Any]]:
        try:
            import re
            json_str = ""
            
            # More robust regex to find JSON array, even if surrounded by other text
            # It looks for the first occurrence of '[' followed by '{' and ends with ']'
            json_match = re.search(r'\[\s*\{[\s\S]*?\}\s*\]', llm_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0) # Get the entire matched JSON array
            
            if not json_str:
                raise ValueError("Could not find a JSON array in the LLM response.")
            
            print(f"DEBUG: Extracted JSON string (before any cleaning): {json_str}")

            # Attempt to parse directly first
            try:
                parsed_data = json.loads(json_str)
                print(f"DEBUG: Successfully parsed JSON directly.")
            except json.JSONDecodeError as e_direct:
                print(f"DEBUG: Direct JSON parse failed: {e_direct}. Attempting to clean and re-parse.")
                
                # Aggressive cleaning: remove all backslashes that are not part of a valid escape sequence
                # This regex targets backslashes that are NOT followed by another backslash or a double quote
                # This is a heuristic and might remove legitimate escapes if the LLM is very inconsistent.
                # A more robust solution would involve a proper JSON parser that can handle lenient parsing.
                cleaned_json_str = re.sub(r'\\(?!["\\])', '', json_str) # Remove backslashes not followed by " or \
                cleaned_json_str = cleaned_json_str.replace('\\"', '"') # Unescape \" to "
                cleaned_json_str = cleaned_json_str.replace('\\\\"', '"') # Unescape \\" to " (if any remain)
                
                # Remove any remaining invalid control characters (e.g., unescaped newlines, tabs)
                cleaned_json_str = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', cleaned_json_str)
                
                print(f"DEBUG: Cleaned JSON string (before final parse): {cleaned_json_str}")
                
                try:
                    parsed_data = json.loads(cleaned_json_str)
                    print(f"DEBUG: Successfully parsed JSON after cleaning.")
                except json.JSONDecodeError as e_cleaned:
                    print(f"DEBUG: Final JSON parse failed after cleaning: {e_cleaned}. Original error: {e_direct}")
                    raise ValueError(f"Failed to parse LLM response as JSON after cleaning: {e_cleaned}")
            
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
                
                # Ensure 'explanation' field is present, even if empty
                if "explanation" not in q:
                    q["explanation"] = ""

                # Ensure correct_answer is a string
                if isinstance(q["correct_answer"], list):
                    # For multiple choice, if it's a list, try to join or take the first element
                    if q["question_type"] == "multiple_choice":
                        if len(q["correct_answer"]) == 1:
                            q["correct_answer"] = str(q["correct_answer"][0])
                        else:
                            # If multiple correct answers are provided for MC, join them
                            q["correct_answer"] = ", ".join(map(str, q["correct_answer"]))
                    else:
                        # For other types, just convert the list to a string representation
                        q["correct_answer"] = ", ".join(map(str, q["correct_answer"]))
                elif not isinstance(q["correct_answer"], str):
                    q["correct_answer"] = str(q["correct_answer"]) # Ensure it's a string

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
            # Return an empty list of questions if parsing fails due to unexpected errors
            return []

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
            suggestion_response = await self.llm_service.generate_response(full_prompt, context={})
            return suggestion_response
        except Exception as e:
            print(f"Error generating study suggestions with LLM: {e}")
            return "Failed to generate study suggestions due to an internal error."
