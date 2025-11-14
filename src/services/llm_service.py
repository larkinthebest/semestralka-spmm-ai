import asyncio
from typing import List, Dict, Any
import json
import os
import openai # Needed for OpenRouter integration (even if commented out for now)
import ollama # Needed for Ollama integration
from gpt4all import GPT4All # Import GPT4All client

class LLMService:
    def __init__(self):
        self.providers_order = [p.strip().lower() for p in os.getenv("LLM_PROVIDERS_ORDER", "gpt4all").split(',')] # Default to gpt4all
        self.active_providers = []
        self.initialized = False

        # GPT4All configuration
        self.gpt4all_model_name = os.getenv("GPT4ALL_MODEL_NAME", "Meta-Llama-3-8B-Instruct.Q4_0.gguf") # Default model
        self.gpt4all_model_path = os.getenv("GPT4ALL_MODEL_PATH", "models/") # Directory to store models
        self.gpt4all_client = None

        # Ollama configuration
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.ollama_model_name = os.getenv("OLLAMA_MODEL_NAME", "llava") # Default to LLaVA for multimodal
        self.ollama_client = None

        # OpenRouter configuration (still commented out as per user request)
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.openrouter_model_name = os.getenv("OPENROUTER_MODEL_NAME", "amazon/nova-premier-v1")
        self.openrouter_client = None

        print(f"DEBUG: LLMService instance created. Provider order: {self.providers_order}")
    
    async def initialize(self):
        """Initialize all configured LLM models and set up fallback order"""
        print(f"DEBUG: Initializing LLMService instance: {id(self)}")
        self.active_providers = []

        for provider_name in self.providers_order:
            if provider_name == "gpt4all":
                try:
                    # GPT4All models are downloaded to the specified model_path
                    self.gpt4all_client = GPT4All(self.gpt4all_model_name, model_path=self.gpt4all_model_path)
                    self.active_providers.append("gpt4all")
                    print(f"✅ GPT4All client initialized successfully for instance: {id(self)}, model: {self.gpt4all_model_name}")
                except Exception as e:
                    print(f"❌ Failed to initialize GPT4All client with model {self.gpt4all_model_name} in path {self.gpt4all_model_path}: {e}")
            elif provider_name == "ollama":
                try:
                    self.ollama_client = ollama.AsyncClient(host=self.ollama_base_url)
                    # Verify model is available
                    models = await self.ollama_client.list()
                    print(f"DEBUG: Ollama models list: {models}") # Added debug print
                    if any(m.model == self.ollama_model_name for m in models['models']): # Corrected access to m.model
                        self.active_providers.append("ollama")
                        print(f"✅ Ollama client initialized successfully for instance: {id(self)}, model: {self.ollama_model_name}")
                    else:
                        print(f"❌ Ollama model '{self.ollama_model_name}' not found. Please pull it using 'ollama pull {self.ollama_model_name}'. Skipping Ollama initialization.")
                except Exception as e:
                    print(f"❌ Failed to initialize Ollama client at {self.ollama_base_url}: {e}")
            elif provider_name == "openrouter": # Still commented out as per user request
                if not self.openrouter_api_key:
                    print("❌ OPENROUTER_API_KEY environment variable not set. Skipping OpenRouter initialization.")
                    continue
                try:
                    self.openrouter_client = openai.AsyncOpenAI(
                        base_url="https://openrouter.ai/api/v1",
                        api_key=self.openrouter_api_key,
                    )
                    self.active_providers.append("openrouter")
                    print(f"✅ OpenRouter client initialized successfully for instance: {id(self)}, model: {self.openrouter_model_name}")
                except Exception as e:
                    print(f"❌ Failed to initialize OpenRouter client: {e}")
            else:
                print(f"⚠️ Unknown LLM provider '{provider_name}' in LLM_PROVIDERS_ORDER. Skipping.")

        if self.active_providers:
            self.initialized = True
            print(f"✅ LLMService initialized with active providers: {self.active_providers}")
        else:
            self.initialized = False
            print("❌ No LLM providers initialized successfully. Using fallback responses for demo purposes.")
    
    async def generate_response(self, prompt: str, context: Any = "") -> str:
        """Generate a response using the configured LLM with fallback"""
        print(f"DEBUG: generate_response called for instance: {id(self)}, initialized: {self.initialized}, active_providers: {self.active_providers}")
        print(f"DEBUG: generate_response - type of context: {type(context)}, context value (truncated): {str(context)[:200]}") # Added debug print
        if not self.initialized:
            return self._fallback_response(prompt, context)
        
        text_content = ""
        base64_images_list = []
        base64_video_frames = []

        if isinstance(context, dict):
            text_content = context.get('content', '')
            single_base64_image = context.get('base64_image')
            if single_base64_image:
                base64_images_list = [single_base64_image]
            base64_video_frames = context.get('base64_video_frames', [])
        elif isinstance(context, str):
            text_content = context
        
        all_base64_visuals = base64_images_list + base64_video_frames

        # Extract system prompt details from the context dictionary
        system_prompt_details = {}
        if isinstance(context, dict):
            system_prompt_details = context.get('system_prompt_details', {})
        
        tutor = system_prompt_details.get('tutor', 'enola')
        mode = system_prompt_details.get('mode', 'explanation')
        language = system_prompt_details.get('language', 'en')
        find_what_i_need = system_prompt_details.get('find_what_i_need', False)

        # Generate the system prompt using the helper function from main.py
        # This requires importing _get_system_prompt from src.api.main
        # For now, I will replicate the logic here to avoid circular imports or complex refactoring.
        # A better long-term solution would be to refactor _get_system_prompt into a shared utility.
        
        system_content = self._build_dynamic_system_prompt(tutor, mode, language, find_what_i_need)

        for provider_name in self.active_providers:
            try:
                if provider_name == "ollama":
                    if not self.ollama_client:
                        print(f"DEBUG: Ollama client not initialized for instance: {id(self)}. Skipping.")
                        continue
                    
                    print(f"DEBUG: Calling Ollama chat with model: {self.ollama_model_name} for instance: {id(self)}")
                    
                    # Prepare messages with images embedded directly in content
                    messages = [] # Initialize messages list
                    if text_content:
                        user_context_max_chars = 10000 # Consistent with other contexts
                        if len(text_content) > user_context_max_chars:
                            text_content = text_content[:user_context_max_chars] + "...[content truncated]"
                        system_content += f"\n\nStudy Material:\n{text_content}"
                    
                    messages.append({"role": "system", "content": system_content})

                    user_message_content = prompt # The original prompt is the user's message
                    if all_base64_visuals:
                        messages.append({
                            "role": "user",
                            "content": user_message_content,
                            "images": [f"data:image/jpeg;base64,{b64_data}" for b64_data in all_base64_visuals]
                        })
                    else:
                        messages.append({"role": "user", "content": user_message_content})
                    
                    response = await self.ollama_client.chat(
                        model=self.ollama_model_name,
                        messages=messages,
                        options={'temperature': 0.7, 'num_predict': 2048}
                    )
                    return response['message']['content'].strip()

                elif provider_name == "gpt4all":
                    if not self.gpt4all_client:
                        print(f"DEBUG: GPT4All client not initialized for instance: {id(self)}. Skipping.")
                        continue
                    
                    # GPT4All uses a single string prompt, so combine system_content and user_message
                    full_prompt_content = system_content
                    if text_content:
                        max_context_chars = 1000 # Adjusted for GPT4All's 2048 token context window.
                        if len(text_content) > max_context_chars:
                            text_content = text_content[:max_context_chars] + "...[content truncated]"
                        full_prompt_content += f"\n\nStudy Material:\n{text_content}"
                    
                    full_prompt = f"{full_prompt_content}\n\nUser: {prompt}\nAssistant:"
                    
                    print(f"DEBUG: Calling GPT4All generate for instance: {id(self)}")
                    
                    # GPT4All generate is synchronous, run in a thread pool executor
                    loop = asyncio.get_running_loop()
                    response_content = await loop.run_in_executor(
                        None, # Use default ThreadPoolExecutor
                        lambda: self.gpt4all_client.generate(full_prompt, max_tokens=2048, temp=0.7)
                    )
                    return response_content.strip()
                
                elif provider_name == "openrouter": # Still commented out as per user request
                    if not self.openrouter_client:
                        print(f"DEBUG: OpenRouter client not initialized for instance: {id(self)}. Skipping.")
                        continue
                    
                    messages = [] # Initialize messages list
                    if text_content:
                        max_context_chars = 20000
                        if len(text_content) > max_context_chars:
                            text_content = text_content[:max_context_chars] + "...[content truncated]"
                        system_content += f"\n\nStudy Material:\n{text_content}"
                    
                    messages.append({"role": "system", "content": system_content})

                    user_content_parts = [{"type": "text", "text": prompt}]
                    if all_base64_visuals:
                        for b64_data in all_base64_visuals:
                            user_content_parts.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_data}"}})
                    
                    messages.append({"role": "user", "content": user_content_parts})

                    print(f"DEBUG: Calling OpenRouter chat.completions.create with model: {self.openrouter_model_name} for instance: {id(self)}")
                    chat_completion = await self.openrouter_client.chat.completions.create(
                        messages=messages,
                        model=self.openrouter_model_name,
                        temperature=0.7,
                        max_tokens=2048,
                    )
                    return chat_completion.choices[0].message.content.strip()

            except Exception as e:
                print(f"Error generating response with {provider_name} for instance: {id(self)}: {e}")
        
        print("❌ All active LLM providers failed. Using fallback response.")
        return self._fallback_response(prompt, context)
    
    def _prepare_gpt4all_prompt(self, user_message: str, context: str = "") -> str:
        """Prepare prompt for GPT4All"""
        # This method is no longer directly used for generate_response, its logic is now inline.
        # Keeping it for _prepare_gpt4all_quiz_prompt for now.
        system_content = """You are a helpful AI tutor. Provide clear, educational responses based on the provided materials.
For mathematical content, use LaTeX syntax: `$...$` for inline math and `$$...$$` for display math.
When outlining tasks or problems, present them clearly with the problem statement, steps for solution, and final answer using LaTeX where appropriate.

**Example for a mathematical task:**
## Task 4: Solving a Differential Equation

**Problem Statement:**
Solve the following second-order linear ordinary differential equation with constant coefficients:
$$x''(t) - 3x'(t) + 2x(t) = 2e^{3t}$$
with initial conditions:
$$x(0+) = 0$$
$$x'(0+) = 0$$

**Solution Steps:**
1. **Find the complementary solution** by solving the homogeneous equation $x''(t) - 3x'(t) + 2x(t) = 0$.
   The characteristic equation is $r^2 - 3r + 2 = 0$, which factors to $(r-1)(r-2) = 0$.
   Thus, $r_1 = 1$ and $r_2 = 2$.
   The complementary solution is $x_c(t) = C_1 e^t + C_2 e^{2t}$.

2. **Find a particular solution** using the method of undetermined coefficients.
   Since the right-hand side is $2e^{3t}$, we assume a particular solution of the form $x_p(t) = A e^{3t}$.
   Then $x_p'(t) = 3A e^{3t}$ and $x_p''(t) = 9A e^{3t}$.
   Substitute these into the differential equation:
   $9A e^{3t} - 3(3A e^{3t}) + 2(A e^{3t}) = 2e^{3t}$
   $9A e^{3t} - 9A e^{3t} + 2A e^{3t} = 2e^{3t}$
   $2A e^{3t} = 2e^{3t} \implies A = 1$.
   So, the particular solution is $x_p(t) = e^{3t}$.

3. **Form the general solution** $x(t) = x_c(t) + x_p(t)$.
   $x(t) = C_1 e^t + C_2 e^{2t} + e^{3t}$.

4. **Apply initial conditions** to find $C_1$ and $C_2$.
   $x(0+) = C_1 e^0 + C_2 e^0 + e^0 = C_1 + C_2 + 1 = 0 \implies C_1 + C_2 = -1$.
   First, find $x'(t) = C_1 e^t + 2C_2 e^{2t} + 3e^{3t}$.
   $x'(0+) = C_1 e^0 + 2C_2 e^0 + 3e^0 = C_1 + 2C_2 + 3 = 0 \implies C_1 + 2C_2 = -3$.
   Solving the system of equations:
   $(C_1 + 2C_2) - (C_1 + C_2) = -3 - (-1)$
   $C_2 = -2$.
   Substitute $C_2 = -2$ into $C_1 + C_2 = -1 \implies C_1 - 2 = -1 \implies C_1 = 1$.

**Final Answer:**
The solution to the differential equation is:
$$x(t) = e^t - 2e^{2t} + e^{3t}$$
"""
        if context:
            # Adjusted for GPT4All's 2048 token context window.
            # A conservative estimate of 1 token per 4 characters, minus system prompt overhead.
            max_context_chars = 1000 # Adjusted for GPT4All's 2048 token context window.
            if len(context) > max_context_chars:
                context = context[:max_context_chars] + "...[content truncated]"
            system_content += f"\n\nStudy Material:\n{context}"
        
        return f"{system_content}\n\nUser: {user_message}\nAssistant:"

    def _prepare_ollama_messages(self, user_message: str, context: Any = "", base64_visuals: List[str] = None) -> List[Dict[str, Any]]:
        """Prepare messages in Ollama chat format (multimodal support, images passed directly in content)"""
        messages = []
        
        system_prompt_details = {}
        if isinstance(context, dict):
            system_prompt_details = context.get('system_prompt_details', {})
        
        tutor = system_prompt_details.get('tutor', 'enola')
        mode = system_prompt_details.get('mode', 'explanation')
        language = system_prompt_details.get('language', 'en')
        find_what_i_need = system_prompt_details.get('find_what_i_need', False)

        system_content = self._build_dynamic_system_prompt(tutor, mode, language, find_what_i_need)

        # Define a consistent max_context_chars for user-provided text context
        user_context_max_chars = 10000 # Increased for Ollama, assuming larger context window

        if isinstance(context, dict) and context.get('content'):
            text_content = context.get('content')
            if len(text_content) > user_context_max_chars:
                text_content = text_content[:user_context_max_chars] + "...[content truncated]"
            system_content += f"\n\nStudy Material:\n{text_content}"
        
        messages.append({"role": "system", "content": system_content})

        user_message_content = user_message
        if base64_visuals:
            # Ollama expects images in a separate 'images' field, not within 'content' list of dicts
            # The 'content' field should be a string for text.
            messages.append({
                "role": "user",
                "content": user_message_content,
                "images": [f"data:image/jpeg;base64,{b64_data}" for b64_data in base64_visuals]
            })
        else:
            messages.append({"role": "user", "content": user_message_content})
        
        return messages

    def _prepare_openrouter_messages(self, user_message: str, context: Any = "", base64_visuals: List[str] = None) -> List[Dict[str, Any]]:
        """Prepare messages in OpenRouter chat format (compatible with OpenAI format)"""
        messages = []
        
        system_prompt_details = {}
        if isinstance(context, dict):
            system_prompt_details = context.get('system_prompt_details', {})
        
        tutor = system_prompt_details.get('tutor', 'enola')
        mode = system_prompt_details.get('mode', 'explanation')
        language = system_prompt_details.get('language', 'en')
        find_what_i_need = system_prompt_details.get('find_what_i_need', False)

        system_content = self._build_dynamic_system_prompt(tutor, mode, language, find_what_i_need)

        if isinstance(context, dict) and context.get('content'):
            max_context_chars = 20000
            text_content = context.get('content')
            if len(text_content) > max_context_chars:
                text_content = text_content[:max_context_chars] + "...[content truncated]"
            system_content += f"\n\nStudy Material:\n{text_content}"
        
        messages.append({"role": "system", "content": system_content})

        user_content_parts = [{"type": "text", "text": user_message}]
        if base64_visuals:
            for b64_data in base64_visuals:
                user_content_parts.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_data}"}})
        
        messages.append({"role": "user", "content": user_content_parts})
        
        return messages
    
    def _build_dynamic_system_prompt(self, tutor: str, mode: str, language: str, find_what_i_need: bool = False) -> str:
        """Generates the system prompt based on tutor, mode, and language."""
        language_instruction = ""
        if language == "de":
            language_instruction = "\n\n**IMPORTANT: Respond in German (Deutsch). Use German language for all explanations and examples.**"
        elif language == "sk":
            language_instruction = "\n\n**IMPORTANT: Respond in Slovak (Slovenčina). Use Slovak language for all explanations and examples.**"
        elif language == "en":
            language_instruction = "\n\n**IMPORTANT: Respond in English.**"
        
        if tutor == "enola" and mode == "explanation":
            if find_what_i_need:
                return f"""You are Enola, a friendly and enthusiastic AI tutor who specializes in finding specific information within provided documents. You have been provided with the content of the attached files. {language_instruction}

**Your role:**
• Directly address the user's request to "find what I need"
• Search through the *provided content from the attached files* for the specific information requested in the user's message.
• Clearly outline where the information was found (e.g., "In file 'document.pdf', on page 3, it states...")
• Provide the relevant information concisely.
• If the information is not found in the *provided content*, state that clearly.
• Be helpful and precise.

**CRITICAL FORMATTING REQUIREMENTS (Format like Amazon Q):**
• Start with a clear ## heading for the main topic
• Use **bold** for important terms and key concepts
• Use bullet points (•) for lists with proper spacing
• Add emojis occasionally to make content engaging (📚 🎯 💡 ✨)
• Use short paragraphs (2-3 sentences) with blank lines between them
• Use ### subheadings to break content into sections
• Add line breaks generously - never create walls of text
• Use numbered lists for sequential steps
• Use > blockquotes for important notes or tips
• Structure: Heading → Brief intro → Sections with subheadings → Lists → Examples
• For mathematical content, use LaTeX syntax: `$...$` for inline math and `$$...$$` for display math.

**Example format:**
## Information Found on [Topic]

I found the following information regarding [topic] in your attached files:

### From [Filename 1]
• On page [X], it states: "[Relevant quote/summary]"
• [Another point]

### From [Filename 2]
• [Relevant information]

Would you like me to elaborate on any of these points or search for something else? 😊"""
            else:
                return f"""You are Enola, a friendly and enthusiastic AI tutor who specializes in explanations. You have been provided with the content of the attached files. {language_instruction}

**Your role:**
• START with concepts from the *provided content of the attached files* as your foundation
• EXPAND and enhance these concepts with additional knowledge and context
• Provide deeper explanations, real-world examples, and practical applications
• Connect file concepts to broader knowledge and current developments
• Use analogies, examples, and clear explanations to aid understanding
• Be warm, encouraging, and make learning enjoyable 😊
• Always reference which parts come from the files vs. your additional insights

**SPECIAL HANDLING FOR TRANSCRIPTION REQUESTS:**
When user asks to "transcribe" or wants "full transcript" or "complete transcription":
• Provide ALL available content from the file, not just summaries
• For videos: Include ALL extracted text, frame descriptions, and OCR content
• For audio: Include ALL transcribed text
• Add timestamps if available in the content (format: [00:00] or 0:00)
• If timestamps aren't in the source, organize content chronologically
• Use clear section breaks for different parts
• DO NOT summarize - provide the COMPLETE content

**CRITICAL FORMATTING REQUIREMENTS (Format like Amazon Q):**
• Start with a clear ## heading for the main topic
• Use **bold** for important terms and key concepts
• Use bullet points (•) for lists with proper spacing
• Add emojis occasionally to make content engaging (📚 🎯 💡 ✨)
• Use short paragraphs (2-3 sentences) with blank lines between them
• Use ### subheadings to break content into sections
• Add line breaks generously - never create walls of text
• Use numbered lists for sequential steps
• Use > blockquotes for important notes or tips
• Structure: Heading → Brief intro → Sections with subheadings → Lists → Examples
• For mathematical content, use LaTeX syntax: `$...$` for inline math and `$$...$$` for display math.

**Example format:**
## Understanding [Concept]

Based on your file, [concept] is... Let me explain this clearly.

### Key Points
• **First point**: Explanation here
• **Second point**: More details

### Real-World Application
In practice, this means... 💡

> **Important**: Remember that...

Would you like me to explain any part in more detail? 😊

**SPECIAL INSTRUCTION FOR MATHEMATICAL CONTENT:**
When presenting mathematical content, ensure it is correctly formatted using LaTeX. Use `$...$` for inline math and `$$...$$` for display math. Pay close attention to superscripts, subscripts, and special symbols, even if the input text from OCR is imperfect. For example, if you see "x''(t) - 3x'(t) + 2x(t) = 2e**3t", interpret it as `$$x''\\left(t\\right) - 3x'\\left(t\\right) + 2x\\left(t\\right) = 2e^{{3t}}$$`.

"""
        elif tutor == "franklin" and mode == "testing":
            return f"""You are Franklin, a methodical AI testing tutor who creates structured quizzes and assessments.{language_instruction}

**ABSOLUTE RULE: NEVER create test questions immediately! ALWAYS ask clarifying questions FIRST!**

**FORBIDDEN BEHAVIOR:**
- DO NOT answer test questions yourself
- DO NOT create quizzes without asking for preferences first
- DO NOT provide direct answers to questions in files
- DO NOT list questions without user's format preference

**REQUIRED BEHAVIOR:**

### When user says "test me on [topic]" or "test me on [topic] from [file]":
You MUST respond with:

## Test Preparation 📝

I'll create a test on **[topic]** from your materials. First, let me clarify your preferences:

**1. Which test format would you prefer?**
• Multiple choice questions
• True/False statements  
• Short answer questions
• Mixed format (combination of all)

**2. How many questions?** (I recommend 5-10)

**3. Difficulty level?**
• Easy (basic concepts)
• Medium (application)
• Hard (analysis and synthesis)

Please let me know your preferences, and I'll create the perfect test for you! 🎯

### When user says just "test me":
You MUST respond with:

## Test Preparation 📝

I'm ready to create a test for you! First, I need some information:

**1. Which topic would you like to be tested on?**
• [List 3-4 main topics from uploaded files]
• Or specify your own topic

**2. What test format do you prefer?**
• Multiple choice
• True/False
• Short answer
• Mixed format

**3. How many questions?** (5-10 recommended)

**4. Difficulty level?**
• Easy • Medium • Hard

Please provide these details so I can create the perfect test for you! 📚

### ONLY create actual quiz AFTER user provides ALL preferences:

📝 **Quiz: [Topic]**

**Question 1:** [Question]
**A)** [Option]
**B)** [Option]
**C)** [Option]
**D)** [Option]

[Continue with remaining questions based on user's chosen format]

**REMEMBER:**
- NEVER answer questions directly
- ALWAYS ask for preferences first
- ONLY create quiz after user confirms format, count, and difficulty
- Use ## headings, **bold**, emojis (📝 🎯 ✨), and proper spacing"""
        else: # Fallback or unexpected combination
            return f"""You are an AI tutor. Respond to the user's message based on the provided study materials.
            Your current mode is '{mode}' and your current tutor is '{tutor}'.{language_instruction}
            
            **Your role:**
            • Provide helpful and informative responses.
            • If in 'explanation' mode, explain concepts clearly.
            • If in 'testing' mode, guide the user towards quiz generation.
            • Always reference which parts come from the files vs. your additional insights.
            
**CRITICAL FORMATTING REQUIREMENTS (Format like Amazon Q):**
• Start with a clear ## heading for the main topic
• Use **bold** for important terms and key concepts
• Use bullet points (•) for lists with proper spacing
• Add emojis occasionally to make content engaging (📚 🎯 💡 ✨)
• Use short paragraphs (2-3 sentences) with blank lines between them
• Use ### subheadings to break content into sections
• Add line breaks generously - never create walls of text
• Use numbered lists for sequential steps
• Use > blockquotes for important notes or tips
• Structure: Heading → Brief intro → Sections with subheadings → Lists → Examples
• For mathematical content, use LaTeX syntax: `$...$` for inline math and `$$...$$` for display math.

**Example format:**
## Understanding [Concept]

Based on your file, [concept] is... Let me explain this clearly.

### Key Points
• **First point**: Explanation here
• **Second point**: More details

### Real-World Application
In practice, this means... 💡

> **Important**: Remember that...

Would you like me to explain any part in more detail? 😊"""
    
    def _fallback_response(self, prompt: str, context: Any = "") -> str: # Changed context type hint to Any
        """Fallback responses when LLM is not available"""
        print(f"DEBUG: Using fallback response for instance: {id(self)}.")
        responses = {
            "hello": "Hello! I'm your AI tutor. How can I help you learn today?",
            "help": "I can help you with:\n• Understanding your study materials\n• Creating quizzes\n• Explaining concepts\n• Answering questions",
            "quiz": "I can generate different types of quizzes from your documents: multiple choice, true/false, and fill-in-the-blank questions.",
            "default": "I'm here to help you learn! Could you please be more specific about what you'd like to know?"
        }
        
        prompt_lower = prompt.lower()
        if isinstance(context, dict):
            context_content = context.get('content', '').lower()
        else:
            context_content = str(context).lower()

        for key, response in responses.items():
            if key in prompt_lower:
                return f"FALLBACK: {response}"
        
        if context_content and "document" in context_content:
            return f"FALLBACK: Based on your document, I can see it contains information about the topic. What specific aspect would you like me to explain?"
        
        return f"FALLBACK: {responses['default']}"

    async def generate_quiz_questions(self, content: str, quiz_type: str, num_questions: int, topic: str = None, difficulty: str = None, language: str = "en") -> Dict[str, Any]:
        """Generate quiz questions from content using the configured LLM with fallback"""
        print(f"DEBUG: generate_quiz_questions called for instance: {id(self)}, initialized: {self.initialized}, active_providers: {self.active_providers}")
        if not self.initialized:
            return {"raw_response_text": "", "error": "LLMService not initialized."}
        
        for provider_name in self.active_providers:
            try:
                if provider_name == "ollama":
                    if not self.ollama_client:
                        print(f"DEBUG: Ollama client not initialized for instance: {id(self)}. Skipping.")
                        continue
                    quiz_messages = self._prepare_ollama_quiz_messages(content, quiz_type, num_questions, topic, difficulty, language)
                    print(f"DEBUG: Calling Ollama chat for quiz with model: {self.ollama_model_name} for instance: {id(self)}")
                    response = await self.ollama_client.chat(
                        model=self.ollama_model_name,
                        messages=quiz_messages,
                        options={'temperature': 0.8, 'num_predict': 2048}
                    )
                    raw_response_text = response['message']['content'].strip()
                    print(f"DEBUG: Raw LLM quiz response (Ollama): {raw_response_text}")
                    return {"raw_response_text": raw_response_text}

                elif provider_name == "gpt4all":
                    if not self.gpt4all_client:
                        print(f"DEBUG: GPT4All client not initialized for instance: {id(self)}. Skipping.")
                        continue
                    
                    quiz_prompt = self._prepare_gpt4all_quiz_prompt(content, quiz_type, num_questions, topic, difficulty, language)
                    print(f"DEBUG: Calling GPT4All generate for quiz with instance: {id(self)}")

                    loop = asyncio.get_running_loop()
                    raw_response_text = await loop.run_in_executor(
                        None,
                        lambda: self.gpt4all_client.generate(quiz_prompt, max_tokens=2048, temp=0.8)
                    )
                    print(f"DEBUG: Raw LLM quiz response (GPT4all): {raw_response_text}")
                    return {"raw_response_text": raw_response_text}

                elif provider_name == "openrouter": # Still commented out as per user request
                    if not self.openrouter_client:
                        print(f"DEBUG: OpenRouter client not initialized for instance: {id(self)}. Skipping.")
                        continue
                    quiz_messages = self._prepare_openrouter_quiz_messages(content, quiz_type, num_questions, topic, difficulty, language)
                    print(f"DEBUG: Calling OpenRouter chat.completions.create for quiz with model: {self.openrouter_model_name} for instance: {id(self)}")
                    chat_completion = await self.openrouter_client.chat.completions.create(
                        messages=quiz_messages,
                        model=self.openrouter_model_name,
                        temperature=0.8,
                        max_tokens=2048,
                        response_format={"type": "json_object"}
                    )
                    raw_response_text = chat_completion.choices[0].message.content.strip()
                    print(f"DEBUG: Raw LLM quiz response (OpenRouter): {raw_response_text}")
                    return {"raw_response_text": raw_response_text}

            except Exception as e:
                print(f"Error generating quiz with {provider_name} for instance: {id(self)}: {e}")
                return {"raw_response_text": "", "error": str(e)} # Return error for quiz_generator to handle
        
        print("❌ All active LLM providers failed for quiz generation. Using fallback quiz questions.")
        return {"raw_response_text": "", "error": "All active LLM providers failed for quiz generation."}
    
    def _prepare_gpt4all_quiz_prompt(self, content: str, quiz_type: str, num_questions: int, topic: str = None, difficulty: str = None, language: str = "en") -> str:
        """Prepare prompt for GPT4all quiz generation"""
        content_snippet = content[:25000]
        
        language_instruction = ""
        if language == "de":
            language_instruction = "The questions and answers MUST be in German. For mathematical content, use LaTeX syntax: `$...$` for inline math and `$$...$$` for display math."
        elif language == "sk":
            language_instruction = "The questions and answers MUST be in Slovak. For mathematical content, use LaTeX syntax: `$...$` for inline math and `$$...$$` for display math."
        elif language == "en":
            language_instruction = "The questions and answers MUST be in English. For mathematical content, use LaTeX syntax: `$...$` for inline math and `$$...$$` for display math."

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
    {
        "question_text": "What is the capital of France?",
        "question_type": "multiple_choice",
        "options": ["Berlin", "Madrid", "Paris", "Rome"],
        "correct_answer": "Paris",
        "explanation": "Paris is the capital and most populous city of France."
    }
]
```

**Example JSON Structure for True/False:**
```json
[
    {
        "question_text": "The Earth is flat.",
        "question_type": "true_false",
        "options": ["True", "False"],
        "correct_answer": "False",
        "explanation": "The Earth is an oblate spheroid, not flat."
    }
]
```

**Example JSON Structure for Fill-in-the-blank:**
```json
[
    {
        "question_text": "The chemical symbol for water is [BLANK].",
        "question_type": "fill_in_the_blank",
        "correct_answer": "H2O",
        "explanation": "Water is a chemical substance with the chemical formula H2O."
    }
]
```

**Example JSON Structure for Short Answer:**
```json
[
    {
        "question_text": "Explain the concept of photosynthesis.",
        "question_type": "short_answer",
        "correct_answer": "Photosynthesis is the process by which green plants and some other organisms use sunlight to synthesize foods with the help of chlorophyll.",
        "explanation": "Photosynthesis is a vital process for life on Earth, converting light energy into chemical energy."
    }
]
```
"""

        system_prompt = f"""
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
        return f"{system_prompt}\nAssistant:"

    def _prepare_ollama_quiz_messages(self, content: str, quiz_type: str, num_questions: int, topic: str = None, difficulty: str = None, language: str = "en") -> List[Dict[str, Any]]:
        """Prepare messages for Ollama quiz generation"""
        content_snippet = content[:25000]
        
        language_instruction = ""
        if language == "de":
            language_instruction = "The questions and answers MUST be in German. For mathematical content, use LaTeX syntax: `$...$` for inline math and `$$...$$` for display math."
        elif language == "sk":
            language_instruction = "The questions and answers MUST be in Slovak. For mathematical content, use LaTeX syntax: `$...$` for inline math and `$$...$$` for display math."
        elif language == "en":
            language_instruction = "The questions and answers MUST be in English. For mathematical content, use LaTeX syntax: `$...$` for inline math and `$$...$$` for display math."

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
    {
        "question_text": "What is the capital of France?",
        "question_type": "multiple_choice",
        "options": ["Berlin", "Madrid", "Paris", "Rome"],
        "correct_answer": "Paris",
        "explanation": "Paris is the capital and most populous city of France."
    }
]
```
"""
        system_prompt = f"""
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
        messages = []
        messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": f"Generate {num_questions} {quiz_type} questions based on the provided content."})
        return messages

    def _prepare_openrouter_quiz_messages(self, content: str, quiz_type: str, num_questions: int, topic: str = None, difficulty: str = None, language: str = "en") -> List[Dict[str, Any]]:
        """Prepare messages for OpenRouter quiz generation (compatible with OpenAI format)"""
        content_snippet = content[:25000]
        
        language_instruction = ""
        if language == "de":
            language_instruction = "The questions and answers MUST be in German. For mathematical content, use LaTeX syntax: `$...$` for inline math and `$$...$$` for display math."
        elif language == "sk":
            language_instruction = "The questions and answers MUST be in Slovak. For mathematical content, use LaTeX syntax: `$...$` for inline math and `$$...$$` for display math."
        elif language == "en":
            language_instruction = "The questions and answers MUST be in English. For mathematical content, use LaTeX syntax: `$...$` for inline math and `$$...$$` for display math."

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
    {
        "question_text": "What is the capital of France?",
        "question_type": "multiple_choice",
        "options": ["Berlin", "Madrid", "Paris", "Rome"],
        "correct_answer": "Paris",
        "explanation": "Paris is the capital and most populous city of France."
    }
]
```
"""
        system_prompt = f"""
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
        return [{"role": "system", "content": system_prompt}]
    
    def _fallback_response(self, prompt: str, context: Any = "") -> str: # Changed context type hint to Any
        """Fallback responses when LLM is not available"""
        print(f"DEBUG: Using fallback response for instance: {id(self)}.")
        responses = {
            "hello": "Hello! I'm your AI tutor. How can I help you learn today?",
            "help": "I can help you with:\n• Understanding your study materials\n• Creating quizzes\n• Explaining concepts\n• Answering questions",
            "quiz": "I can generate different types of quizzes from your documents: multiple choice, true/false, and fill-in-the-blank questions.",
            "default": "I'm here to help you learn! Could you please be more specific about what you'd like to know?"
        }
        
        prompt_lower = prompt.lower()
        if isinstance(context, dict):
            context_content = context.get('content', '').lower()
        else:
            context_content = str(context).lower()

        for key, response in responses.items():
            if key in prompt_lower:
                return f"FALLBACK: {response}"
        
        if context_content and "document" in context_content:
            return f"FALLBACK: Based on your document, I can see it contains information about the topic. What specific aspect would you like me to explain?"
        
        return f"FALLBACK: {responses['default']}"

    async def generate_quiz_questions(self, content: str, quiz_type: str, num_questions: int, topic: str = None, difficulty: str = None, language: str = "en") -> Dict[str, Any]:
        """Generate quiz questions from content using the configured LLM with fallback"""
        print(f"DEBUG: generate_quiz_questions called for instance: {id(self)}, initialized: {self.initialized}, active_providers: {self.active_providers}")
        if not self.initialized:
            return {"raw_response_text": "", "error": "LLMService not initialized."}
        
        for provider_name in self.active_providers:
            try:
                if provider_name == "ollama":
                    if not self.ollama_client:
                        print(f"DEBUG: Ollama client not initialized for instance: {id(self)}. Skipping.")
                        continue
                    quiz_messages = self._prepare_ollama_quiz_messages(content, quiz_type, num_questions, topic, difficulty, language)
                    print(f"DEBUG: Calling Ollama chat for quiz with model: {self.ollama_model_name} for instance: {id(self)}")
                    response = await self.ollama_client.chat(
                        model=self.ollama_model_name,
                        messages=quiz_messages,
                        options={'temperature': 0.8, 'num_predict': 2048}
                    )
                    raw_response_text = response['message']['content'].strip()
                    print(f"DEBUG: Raw LLM quiz response (Ollama): {raw_response_text}")
                    return {"raw_response_text": raw_response_text}

                elif provider_name == "gpt4all":
                    if not self.gpt4all_client:
                        print(f"DEBUG: GPT4All client not initialized for instance: {id(self)}. Skipping.")
                        continue
                    
                    quiz_prompt = self._prepare_gpt4all_quiz_prompt(content, quiz_type, num_questions, topic, difficulty, language)
                    print(f"DEBUG: Calling GPT4All generate for quiz with instance: {id(self)}")

                    loop = asyncio.get_running_loop()
                    raw_response_text = await loop.run_in_executor(
                        None,
                        lambda: self.gpt4all_client.generate(quiz_prompt, max_tokens=2048, temp=0.8)
                    )
                    print(f"DEBUG: Raw LLM quiz response (GPT4all): {raw_response_text}")
                    return {"raw_response_text": raw_response_text}

                elif provider_name == "openrouter": # Still commented out as per user request
                    if not self.openrouter_client:
                        print(f"DEBUG: OpenRouter client not initialized for instance: {id(self)}. Skipping.")
                        continue
                    quiz_messages = self._prepare_openrouter_quiz_messages(content, quiz_type, num_questions, topic, difficulty, language)
                    print(f"DEBUG: Calling OpenRouter chat.completions.create for quiz with model: {self.openrouter_model_name} for instance: {id(self)}")
                    chat_completion = await self.openrouter_client.chat.completions.create(
                        messages=quiz_messages,
                        model=self.openrouter_model_name,
                        temperature=0.8,
                        max_tokens=2048,
                        response_format={"type": "json_object"}
                    )
                    raw_response_text = chat_completion.choices[0].message.content.strip()
                    print(f"DEBUG: Raw LLM quiz response (OpenRouter): {raw_response_text}")
                    return {"raw_response_text": raw_response_text}

            except Exception as e:
                print(f"Error generating quiz with {provider_name} for instance: {id(self)}: {e}")
                return {"raw_response_text": "", "error": str(e)} # Return error for quiz_generator to handle
        
        print("❌ All active LLM providers failed for quiz generation. Using fallback quiz questions.")
        return {"raw_response_text": "", "error": "All active LLM providers failed for quiz generation."}
    
    def _prepare_gpt4all_quiz_prompt(self, content: str, quiz_type: str, num_questions: int, topic: str = None, difficulty: str = None, language: str = "en") -> str:
        """Prepare prompt for GPT4all quiz generation"""
        content_snippet = content[:25000]
        
        language_instruction = ""
        if language == "de":
            language_instruction = "The questions and answers MUST be in German. For mathematical content, use LaTeX syntax: `$...$` for inline math and `$$...$$` for display math."
        elif language == "sk":
            language_instruction = "The questions and answers MUST be in Slovak. For mathematical content, use LaTeX syntax: `$...$` for inline math and `$$...$$` for display math."
        elif language == "en":
            language_instruction = "The questions and answers MUST be in English. For mathematical content, use LaTeX syntax: `$...$` for inline math and `$$...$$` for display math."

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
    {
        "question_text": "What is the capital of France?",
        "question_type": "multiple_choice",
        "options": ["Berlin", "Madrid", "Paris", "Rome"],
        "correct_answer": "Paris",
        "explanation": "Paris is the capital and most populous city of France."
    }
]
```

**Example JSON Structure for True/False:**
```json
[
    {
        "question_text": "The Earth is flat.",
        "question_type": "true_false",
        "options": ["True", "False"],
        "correct_answer": "False",
        "explanation": "The Earth is an oblate spheroid, not flat."
    }
]
```

**Example JSON Structure for Fill-in-the-blank:**
```json
[
    {
        "question_text": "The chemical symbol for water is [BLANK].",
        "question_type": "fill_in_the_blank",
        "correct_answer": "H2O",
        "explanation": "Water is a chemical substance with the chemical formula H2O."
    }
]
```

**Example JSON Structure for Short Answer:**
```json
[
    {
        "question_text": "Explain the concept of photosynthesis.",
        "question_type": "short_answer",
        "correct_answer": "Photosynthesis is the process by which green plants and some other organisms use sunlight to synthesize foods with the help of chlorophyll.",
        "explanation": "Photosynthesis is a vital process for life on Earth, converting light energy into chemical energy."
    }
]
```
"""

        system_prompt = f"""
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
        return f"{system_prompt}\nAssistant:"

    def _prepare_ollama_quiz_messages(self, content: str, quiz_type: str, num_questions: int, topic: str = None, difficulty: str = None, language: str = "en") -> List[Dict[str, Any]]:
        """Prepare messages for Ollama quiz generation"""
        content_snippet = content[:25000]
        
        language_instruction = ""
        if language == "de":
            language_instruction = "The questions and answers MUST be in German. For mathematical content, use LaTeX syntax: `$...$` for inline math and `$$...$$` for display math."
        elif language == "sk":
            language_instruction = "The questions and answers MUST be in Slovak. For mathematical content, use LaTeX syntax: `$...$` for inline math and `$$...$$` for display math."
        elif language == "en":
            language_instruction = "The questions and answers MUST be in English. For mathematical content, use LaTeX syntax: `$...$` for inline math and `$$...$$` for display math."

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
    {
        "question_text": "What is the capital of France?",
        "question_type": "multiple_choice",
        "options": ["Berlin", "Madrid", "Paris", "Rome"],
        "correct_answer": "Paris",
        "explanation": "Paris is the capital and most populous city of France."
    }
]
```
"""
        system_prompt = f"""
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
        messages = []
        messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": f"Generate {num_questions} {quiz_type} questions based on the provided content."})
        return messages

    def _prepare_openrouter_quiz_messages(self, content: str, quiz_type: str, num_questions: int, topic: str = None, difficulty: str = None, language: str = "en") -> List[Dict[str, Any]]:
        """Prepare messages for OpenRouter quiz generation (compatible with OpenAI format)"""
        content_snippet = content[:25000]
        
        language_instruction = ""
        if language == "de":
            language_instruction = "The questions and answers MUST be in German. For mathematical content, use LaTeX syntax: `$...$` for inline math and `$$...$$` for display math."
        elif language == "sk":
            language_instruction = "The questions and answers MUST be in Slovak. For mathematical content, use LaTeX syntax: `$...$` for inline math and `$$...$$` for display math."
        elif language == "en":
            language_instruction = "The questions and answers MUST be in English. For mathematical content, use LaTeX syntax: `$...$` for inline math and `$$...$$` for display math."

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
    {
        "question_text": "What is the capital of France?",
        "question_type": "multiple_choice",
        "options": ["Berlin", "Madrid", "Paris", "Rome"],
        "correct_answer": "Paris",
        "explanation": "Paris is the capital and most populous city of France."
    }
]
```
"""
        system_prompt = f"""
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
        return [{"role": "system", "content": system_prompt}]
    
    def _fallback_response(self, prompt: str, context: Any = "") -> str: # Changed context type hint to Any
        """Fallback responses when LLM is not available"""
        print(f"DEBUG: Using fallback response for instance: {id(self)}.")
        responses = {
            "hello": "Hello! I'm your AI tutor. How can I help you learn today?",
            "help": "I can help you with:\n• Understanding your study materials\n• Creating quizzes\n• Explaining concepts\n• Answering questions",
            "quiz": "I can generate different types of quizzes from your documents: multiple choice, true/false, and fill-in-the-blank questions.",
            "default": "I'm here to help you learn! Could you please be more specific about what you'd like to know?"
        }
        
        prompt_lower = prompt.lower()
        if isinstance(context, dict):
            context_content = context.get('content', '').lower()
        else:
            context_content = str(context).lower()

        for key, response in responses.items():
            if key in prompt_lower:
                return f"FALLBACK: {response}"
        
        if context_content and "document" in context_content:
            return f"FALLBACK: Based on your document, I can see it contains information about the topic. What specific aspect would you like me to explain?"
        
        return f"FALLBACK: {responses['default']}"
