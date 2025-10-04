import asyncio
from typing import Optional
import json

class LLMService:
    def __init__(self):
        self.model = None
        self.initialized = False
    
    async def initialize(self):
        """Initialize the local LLM model"""
        try:
            from gpt4all import GPT4All
            # Use a current model that exists (will auto-download on first use)
            # Try multiple models in order of preference
            models_to_try = [
                "mistral-7b-openorca.gguf2.Q4_0.gguf",
                "orca-mini-3b-gguf2-q4_0.gguf",
                "gpt4all-falcon-newbpe-q4_0.gguf"
            ]
            
            for model_name in models_to_try:
                try:
                    print(f"🔄 Trying to load model: {model_name}")
                    self.model = GPT4All(model_name)
                    self.initialized = True
                    print(f"✅ GPT4All model loaded successfully: {model_name}")
                    break
                except Exception as model_error:
                    print(f"❌ Failed to load {model_name}: {model_error}")
                    continue
            
            if not self.initialized:
                raise Exception("No working models found")
                
        except Exception as e:
            print(f"❌ Failed to load any GPT4All model: {e}")
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

    async def generate_quiz_questions(self, content: str, quiz_type: str, num_questions: int) -> list:
        """Generate quiz questions from content"""
        if not self.initialized:
            return self._fallback_quiz_questions(content, quiz_type, num_questions)
        
        try:
            prompt = self._prepare_quiz_prompt(content, quiz_type, num_questions)
            response = self.model.generate(
                prompt,
                max_tokens=2048,  # Increased for detailed quiz generation
                temp=0.8,
                top_p=0.9
            )
            
            # Parse the response to extract questions
            return self._parse_quiz_response(response, quiz_type)
        except Exception as e:
            print(f"Error generating quiz: {e}")
            return self._fallback_quiz_questions(content, quiz_type, num_questions)
    
    def _prepare_quiz_prompt(self, content: str, quiz_type: str, num_questions: int) -> str:
        """Prepare prompt for quiz generation"""
        content_snippet = content[:15000]  # Much larger content for comprehensive quiz generation
        
        if quiz_type == "multiple_choice":
            return f"""Create {num_questions} multiple choice questions based on this content:

{content_snippet}

Format each question as:
Q: [Question]
A) [Option 1]
B) [Option 2] 
C) [Option 3]
D) [Option 4]
Correct: [Letter]

"""
        elif quiz_type == "true_false":
            return f"""Create {num_questions} true/false questions based on this content:

{content_snippet}

Format each question as:
Q: [Statement]
Answer: True/False

"""
        else:  # fill_blank
            return f"""Create {num_questions} fill-in-the-blank questions based on this content:

{content_snippet}

Format each question as:
Q: [Question with _____ for blank]
Answer: [Correct word/phrase]

"""
    
    def _parse_quiz_response(self, response: str, quiz_type: str) -> list:
        """Parse LLM response into structured quiz questions"""
        questions = []
        lines = response.strip().split('\n')
        
        current_question = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('Q:'):
                if current_question:
                    questions.append(current_question)
                current_question = {"question": line[2:].strip()}
                
            elif quiz_type == "multiple_choice":
                if line.startswith(('A)', 'B)', 'C)', 'D)')):
                    if "options" not in current_question:
                        current_question["options"] = []
                    current_question["options"].append(line[2:].strip())
                elif line.startswith('Correct:'):
                    current_question["correct_answer"] = line[8:].strip()
                    
            elif quiz_type == "true_false":
                if line.startswith('Answer:'):
                    current_question["correct_answer"] = line[7:].strip()
                    current_question["options"] = ["True", "False"]
                    
            elif quiz_type == "fill_blank":
                if line.startswith('Answer:'):
                    current_question["correct_answer"] = line[7:].strip()
        
        if current_question:
            questions.append(current_question)
            
        return questions[:5]  # Limit to requested number
    
    def _fallback_quiz_questions(self, content: str, quiz_type: str, num_questions: int) -> list:
        """Generate fallback quiz questions"""
        if quiz_type == "multiple_choice":
            return [
                {
                    "question": "What is the main topic of this document?",
                    "options": ["Topic A", "Topic B", "Topic C", "Topic D"],
                    "correct_answer": "A"
                },
                {
                    "question": "Which concept is most important?",
                    "options": ["Concept 1", "Concept 2", "Concept 3", "Concept 4"],
                    "correct_answer": "B"
                }
            ][:num_questions]
        
        elif quiz_type == "true_false":
            return [
                {
                    "question": "The document contains important information.",
                    "options": ["True", "False"],
                    "correct_answer": "True"
                },
                {
                    "question": "This is a complex topic that requires study.",
                    "options": ["True", "False"],
                    "correct_answer": "True"
                }
            ][:num_questions]
        
        else:  # fill_blank
            return [
                {
                    "question": "The main concept discussed is _____.",
                    "correct_answer": "learning"
                },
                {
                    "question": "Students should _____ the material carefully.",
                    "correct_answer": "study"
                }
            ][:num_questions]