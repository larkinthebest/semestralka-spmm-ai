import asyncio
from typing import Optional, List, Dict, Any
import json

class LLMService:
    def __init__(self):
        self.model = None
        self.initialized = False
    
    async def initialize(self):
        """Initialize the local LLM model (GPT4All)"""
        try:
            from gpt4all import GPT4All
            # Use a current model that exists (will auto-download on first use)
            # Use a single model as specified in Makefile for space preservation
            # The Makefile now downloads only 'mistral-7b-openorca.gguf2.Q4_0.gguf'
            model_name = "mistral-7b-openorca.gguf2.Q4_0.gguf"
            
            try:
                print(f"🔄 Trying to load model: {model_name}")
                self.model = GPT4All(model_name)
                self.initialized = True
                print(f"✅ GPT4All model loaded successfully: {model_name}")
            except Exception as model_error:
                print(f"❌ Failed to load {model_name}: {model_error}")
                raise Exception(f"Failed to load the specified GPT4All model: {model_name}")
                
        except Exception as e:
            print(f"❌ Failed to initialize GPT4All model: {e}")
            print("📝 Using fallback responses for demo purposes")
            self.initialized = False
    
    async def generate_response(self, prompt: str, context: str = "") -> str:
        """Generate a response using the local LLM"""
        if not self.initialized:
            return self._fallback_response(prompt, context)
        
        try:
            # Prepare the full prompt with context and token management
            full_prompt = self._prepare_prompt(prompt, context)
            
            # Ensure prompt fits in 16K context window
            max_prompt_chars = 60000  # 16K tokens = ~60K characters
            if len(full_prompt) > max_prompt_chars:
                # Truncate context while keeping system prompt and user message
                system_part = full_prompt.split("Context from document:")[0]
                user_part = full_prompt.split("Student:")[-1] if "Student:" in full_prompt else prompt
                
                available_chars = max_prompt_chars - len(system_part) - len(user_part) - 200
                if available_chars > 0 and context:
                    truncated_context = context[:available_chars] + "...[truncated]"
                    full_prompt = f"{system_part}Context from document:\n{truncated_context}\n\nStudent:{user_part}"
                else:
                    full_prompt = f"{system_part}Student:{user_part}"
            
            # Generate response using GPT4All
            response = self.model.generate(
                full_prompt,
                max_tokens=4096,  # Increased for 16K context
                temp=0.7,
                top_p=0.9,
                repeat_penalty=1.1
            )
            
            return response.strip() if response else self._fallback_response(prompt, context)
            
        except Exception as e:
            print(f"Error generating response: {e}")
            return self._fallback_response(prompt, context)
    
    def _prepare_prompt(self, user_message: str, context: str = "") -> str:
        """Prepare the prompt with context and instructions"""
        system_prompt = """You are a helpful AI tutor. Provide clear, educational responses based on the provided materials.

"""
        
        if context:
            # Limit context size to prevent token overflow
            max_context_chars = 4000
            if len(context) > max_context_chars:
                context = context[:max_context_chars] + "...[content truncated]"
            system_prompt += f"Study Material:\n{context}\n\n"
        
        return f"{system_prompt}Question: {user_message}\nAnswer:"
    
    def _fallback_response(self, prompt: str, context: str = "") -> str:
        """Fallback responses when LLM is not available"""
        responses = {
            "hello": "Hello! I'm your AI tutor. How can I help you learn today?",
            "help": "I can help you with:\n• Understanding your study materials\n• Creating quizzes\n• Explaining concepts\n• Answering questions",
            "quiz": "I can generate different types of quizzes from your documents: multiple choice, true/false, and fill-in-the-blank questions.",
            "default": "I'm here to help you learn! Could you please be more specific about what you'd like to know?"
        }
        
        prompt_lower = prompt.lower()
        for key, response in responses.items():
            if key in prompt_lower:
                return response
        
        if context:
            return f"Based on your document, I can see it contains information about the topic. What specific aspect would you like me to explain?"
        
        return responses["default"]

    async def generate_quiz_questions(self, content: str, quiz_type: str, num_questions: int, topic: str = None, difficulty: str = None, language: str = "en") -> Dict[str, Any]:
        """Generate quiz questions from content"""
        if not self.initialized:
            return {"questions": self._fallback_quiz_questions(content, quiz_type, num_questions)}
        
        try:
            prompt = self._prepare_quiz_prompt(content, quiz_type, num_questions, topic, difficulty, language)
            response = self.model.generate(
                prompt,
                max_tokens=2048,  # Increased for detailed quiz generation
                temp=0.8,
                top_p=0.9
            )
            print(f"DEBUG: Raw LLM quiz response: {response}") # Added debug print
            # Parse the response to extract questions and wrap in a dictionary
            parsed_questions = self._parse_quiz_response(response, quiz_type, num_questions)
            return {"questions": parsed_questions}
        except Exception as e:
            print(f"Error generating quiz: {e}")
            return {"questions": self._fallback_quiz_questions(content, quiz_type, num_questions)}
    
    def _prepare_quiz_prompt(self, content: str, quiz_type: str, num_questions: int, topic: str = None, difficulty: str = None, language: str = "en") -> str:
        """Prepare prompt for quiz generation"""
        content_snippet = content[:15000]  # Much larger content for comprehensive quiz generation
        
        language_instruction = ""
        if language == "de":
            language_instruction = "The questions and answers MUST be in German."
        elif language == "sk":
            language_instruction = "The questions and answers MUST be in Slovak."
        elif language == "en":
            language_instruction = "The questions and answers MUST be in English."

        topic_instruction = f" on the topic of '{topic}'" if topic else ""
        difficulty_instruction = f" with '{difficulty}' difficulty" if difficulty else ""

        json_format_instructions = """
**CRITICAL INSTRUCTIONS FOR JSON OUTPUT:**
- The output MUST be a JSON array of question objects.
- Do NOT include any other text, markdown, or conversational elements outside the JSON array.
- Each question object MUST include `question_text`, `question_type`, `correct_answer`, and `explanation`.
- For 'multiple_choice' questions, include an `options` list with 4 distinct choices.
- For 'true_false' questions, the `options` list MUST be `["True", "False"]`.
- For 'fill_in_the_blank' questions, indicate the blank with `[BLANK]` in `question_text` and provide the missing word/phrase as `correct_answer`. Do NOT include options.
- For 'short_answer' questions, `options` can be omitted.
- The `explanation` should be a concise, helpful explanation for the correct answer.

**Example JSON Structure for Multiple Choice:**
```json
[
    {{
        "question_text": "What is the capital of France?",
        "question_type": "multiple_choice",
        "options": ["Berlin", "Madrid", "Paris", "Rome"],
        "correct_answer": "Paris",
        "explanation": "Paris is the capital and most populous city of France."
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
        "correct_answer": "False",
        "explanation": "The Earth is an oblate spheroid, not flat."
    }}
]
```

**Example JSON Structure for Fill-in-the-blank:**
```json
[
    {{
        "question_text": "The chemical symbol for water is [BLANK].",
        "question_type": "fill_in_the_blank",
        "correct_answer": "H2O",
        "explanation": "Water is a chemical substance with the chemical formula H2O."
    }}
]
```

**Example JSON Structure for Short Answer:**
```json
[
    {{
        "question_text": "Explain the concept of photosynthesis.",
        "question_type": "short_answer",
        "correct_answer": "Photosynthesis is the process by which green plants and some other organisms use sunlight to synthesize foods with the help of chlorophyll.",
        "explanation": "Photosynthesis is a vital process for life on Earth, converting light energy into chemical energy."
    }}
]
```
"""

        base_prompt = f"""
You are an expert quiz generator. Your task is to create a quiz with exactly {num_questions} questions of type '{quiz_type}' {topic_instruction} {difficulty_instruction} based STRICTLY ONLY on the provided content.
{language_instruction}

**ABSOLUTE CRITICAL RULE: ALL questions MUST be derived SOLELY and DIRECTLY from the "Provided Content" section. You are STRICTLY FORBIDDEN from using any general knowledge, external information, or making up questions not explicitly supported by the text. If the provided content is insufficient to generate {num_questions} questions, generate fewer questions or none at all. DO NOT invent questions. Any deviation from this rule will result in a penalty. If the content is too short or irrelevant to the topic, you MUST respond with an empty JSON array `[]` and NO other text.**

**SPECIFIC NEGATIVE CONSTRAINTS (DO NOT generate these types of questions):**
- DO NOT ask "What is the main topic of this document?" or similar generic questions.
- DO NOT ask "Summarize the document." or similar summary-based questions.
- DO NOT ask questions that can be answered without reading the provided content (e.g., "What is the capital of France?" unless France is explicitly discussed in the content).
- DO NOT ask questions about the number of sections, pages, or general structure of the document.

**IMPORTANT: Adherence to Quiz Type**
- If `quiz_type` is 'true_false', absolutely DO NOT generate 'multiple_choice', 'fill_in_the_blank', or 'short_answer' questions.
- If `quiz_type` is 'multiple_choice', absolutely DO NOT generate 'true_false', 'fill_in_the_blank', or 'short_answer' questions.
- If `quiz_type` is 'fill_in_the_blank', absolutely DO NOT generate 'multiple_choice', 'true_false', or 'short_answer' questions.
- If `quiz_type` is 'short_answer', absolutely DO NOT generate 'multiple_choice', 'true_false', or 'fill_in_the_blank' questions.

{json_format_instructions}

**Provided Content:**
---
{content_snippet}
---

Generate the {quiz_type} quiz questions in JSON format:
"""
        return base_prompt
    
    def _parse_quiz_response(self, response: str, quiz_type: str, num_questions: int) -> List[Dict[str, Any]]:
        """Parse LLM response into structured quiz questions (expecting JSON from GPT4All)"""
        try:
            # Attempt to find the JSON array in the response
            import re
            json_str = ""
            
            # First, try to extract JSON from a markdown code block
            json_match = re.search(r'```json\s*(\[[\s\S]*?\])\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # If no markdown block, try to find a standalone JSON array
                json_match = re.search(r'(\[\s*\{[\s\S]*?\}\s*\])', response, re.DOTALL)
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
                json_str = re.sub(r'("question_text":\s*".*?)"(.*?)"', r'\1\\"\2"', json_str, flags=re.DOTALL)
                json_str = re.sub(r'("correct_answer":\s*".*?)"(.*?)"', r'\1\\"\2"', json_str, flags=re.DOTALL)
                json_str = re.sub(r'("explanation":\s*".*?)"(.*?)"', r'\1\\"\2"', json_str, flags=re.DOTALL)
                json_str = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', json_str) # Remove invalid control characters
                print(f"DEBUG: Extracted and aggressively cleaned JSON string: {json_str}")
                parsed_data = json.loads(json_str)
            
            if not isinstance(parsed_data, list):
                raise ValueError("LLM response is not a JSON array.")
            
            # Post-generation validation and filtering for generic questions and type adherence
            filtered_data = []
            generic_question_keywords = [
                "main topic", "summarize", "main idea", "what is this document about",
                "number of sections", "number of pages", "structure of the document"
            ]

            for q in parsed_data:
                if not all(k in q for k in ["question_text", "question_type", "correct_answer"]):
                    print(f"Warning: Missing required fields in a question object: {q}. Skipping.")
                    continue
                if q["question_type"] == "multiple_choice" and "options" not in q:
                    print(f"Warning: Multiple choice question missing options: {q}. Skipping.")
                    continue
                if q["question_type"] == "true_false":
                    if q.get("options") != ["True", "False"]:
                        print(f"Warning: True/False question options not as expected: {q.get('options')}. Forcing to ['True', 'False'].")
                        q["options"] = ["True", "False"]
                
                is_generic = False
                for keyword in generic_question_keywords:
                    if keyword in q["question_text"].lower():
                        is_generic = True
                        break
                
                if is_generic:
                    print(f"Warning: Detected generic question: '{q['question_text']}'. Skipping.")
                    continue
                
                if q["question_type"] != quiz_type:
                    print(f"Warning: Question type mismatch. Expected '{quiz_type}', got '{q['question_type']}'. Skipping question: '{q['question_text']}'.")
                    continue

                filtered_data.append(q)
            
            return filtered_data[:num_questions] # Limit to requested number after filtering
        except json.JSONDecodeError as e:
            print(f"JSON decoding error: {e}")
            print(f"Problematic LLM response: {response}")
            raise ValueError(f"Failed to parse LLM response as JSON: {e}")
        except ValueError as e:
            print(f"Validation error in parsed quiz data: {e}")
            print(f"Problematic LLM response: {response}")
            raise ValueError(f"Invalid quiz data structure from LLM: {e}")
        except Exception as e:
            print(f"Unexpected error parsing LLM response: {e}")
            print(f"Problematic LLM response: {response}")
            raise ValueError(f"An unexpected error occurred during parsing: {e}")
    
    def _fallback_quiz_questions(self, content: str, quiz_type: str, num_questions: int) -> List[Dict[str, Any]]:
        """Generate fallback quiz questions"""
        if quiz_type == "multiple_choice":
            return [
                {
                    "question_text": "What is the main topic of this document?",
                    "options": ["Topic A", "Topic B", "Topic C", "Topic D"],
                    "correct_answer": "A",
                    "question_type": "multiple_choice",
                    "explanation": "This is a fallback explanation."
                },
                {
                    "question_text": "Which concept is most important?",
                    "options": ["Concept 1", "Concept 2", "Concept 3", "Concept 4"],
                    "correct_answer": "B",
                    "question_type": "multiple_choice",
                    "explanation": "This is a fallback explanation."
                }
            ][:num_questions]
        
        elif quiz_type == "true_false":
            return [
                {
                    "question_text": "The document contains important information.",
                    "options": ["True", "False"],
                    "correct_answer": "True",
                    "question_type": "true_false",
                    "explanation": "This is a fallback explanation."
                },
                {
                    "question_text": "This is a complex topic that requires study.",
                    "options": ["True", "False"],
                    "correct_answer": "True",
                    "question_type": "true_false",
                    "explanation": "This is a fallback explanation."
                }
            ][:num_questions]
        
        elif quiz_type == "fill_in_the_blank": # Corrected from "fill_blank"
            return [
                {
                    "question_text": "The main concept discussed is [BLANK].",
                    "correct_answer": "learning",
                    "question_type": "fill_in_the_blank", # Corrected from "fill_blank"
                    "explanation": "This is a fallback explanation."
                },
                {
                    "question_text": "Students should [BLANK] the material carefully.",
                    "correct_answer": "study",
                    "question_type": "fill_in_the_blank", # Corrected from "fill_blank"
                    "explanation": "This is a fallback explanation."
                }
            ][:num_questions]
        else: # short_answer
            return [
                {
                    "question_text": "Explain the main idea of the document in your own words.",
                    "correct_answer": "Varies",
                    "question_type": "short_answer",
                    "explanation": "This is a fallback explanation."
                },
                {
                    "question_text": "Summarize the key takeaways from the content.",
                    "correct_answer": "Varies",
                    "question_type": "short_answer",
                    "explanation": "This is a fallback explanation."
                }
            ][:num_questions]
