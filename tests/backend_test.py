import httpx
import asyncio
import os
import json

# Ensure the API key is loaded from .env for this script
from dotenv import load_dotenv
load_dotenv()

API_BASE_URL = "http://localhost:8002"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

async def run_backend_tests():
    print("Starting backend tests...")

    # 1. Register a new user
    print("\n--- Registering new user ---")
    register_data = {
        "email": "testuser@example.com",
        "username": "testuser",
        "password": "testpassword"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{API_BASE_URL}/auth/register", json=register_data)
            response.raise_for_status()
            user_info = response.json()
            print(f"User registered: {user_info}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400 and "Email already registered" in e.response.text:
                print("User already registered, proceeding to login.")
            else:
                print(f"Error registering user: {e.response.status_code} - {e.response.text}")
                return
        except Exception as e:
            import traceback
            print(f"An unexpected error occurred during registration: {e}")
            traceback.print_exc()
            return

        # 2. Log in to get an access token
        print("\n--- Logging in ---")
        login_data = {
            "email": "testuser@example.com",
            "password": "testpassword"
        }
        try:
            response = await client.post(f"{API_BASE_URL}/auth/login", json=login_data)
            response.raise_for_status()
            login_info = response.json()
            access_token = login_info["access_token"]
            print(f"Logged in successfully. Access token: {access_token[:10]}...")
        except httpx.HTTPStatusError as e:
            print(f"Error logging in: {e.response.status_code} - {e.response.text}")
            return
        except Exception as e:
            import traceback
            print(f"An unexpected error occurred during login: {e}")
            traceback.print_exc()
            return

        headers = {"Authorization": f"Bearer {access_token}"}

        # 3. Create a new chat
        print("\n--- Creating new chat ---")
        try:
            response = await client.post(f"{API_BASE_URL}/chats/new", headers=headers)
            response.raise_for_status()
            chat_info = response.json()
            chat_id = chat_info["chat_id"]
            print(f"New chat created: {chat_info}")
        except httpx.HTTPStatusError as e:
            print(f"Error creating new chat: {e.response.status_code} - {e.response.text}")
            return
        except Exception as e:
            import traceback
            print(f"An unexpected error occurred during chat creation: {e}")
            traceback.print_exc()
            return

        # 4. Upload a simple file
        print("\n--- Uploading simple file (ai_concepts.md) ---")
        file_path = "samples/ai_concepts.md"
        try:
            with open(file_path, "rb") as f:
                files = {"file": (os.path.basename(file_path), f, "application/octet-stream")}
                response = await client.post(f"{API_BASE_URL}/documents/upload", headers=headers, files=files)
                response.raise_for_status()
                upload_info = response.json()
                print(f"File uploaded: {upload_info}")
                uploaded_filename = upload_info["filename"]
        except httpx.HTTPStatusError as e:
            print(f"Error uploading file: {e.response.status_code} - {e.response.text}")
            return
        except FileNotFoundError:
            print(f"Error: File not found at {file_path}. Please ensure it exists.")
            return
        except Exception as e:
            import traceback
            print(f"An unexpected error occurred during file upload: {e}")
            traceback.print_exc()
            return

        # 5. Send a simple chat message (explanation mode)
        print("\n--- Sending simple chat message (explanation mode) ---")
        chat_message_data = {
            "message": "Explain the core concepts of AI from the uploaded file.",
            "mode": "explanation",
            "tutor": "enola",
            "chat_id": chat_id,
            "attached_files": [uploaded_filename],
            "language": "en"
        }
        try:
            response = await client.post(f"{API_BASE_URL}/simple-chat", headers=headers, json=chat_message_data)
            print(f"DEBUG: Simple chat (explanation) response status: {response.status_code}")
            print(f"DEBUG: Simple chat (explanation) raw response text: {response.text}")
            response.raise_for_status()
            chat_response = response.json()
            print(f"Chat response (explanation): {chat_response['response'][:200]}...")
        except httpx.HTTPStatusError as e:
            print(f"Error in simple chat (explanation): {e.response.status_code} - {e.response.text}")
            return
        except json.JSONDecodeError as e:
            print(f"JSON decoding error for simple chat (explanation): {e}")
            print(f"Problematic response text: {response.text}")
            return
        except Exception as e:
            import traceback
            print(f"An unexpected error occurred during simple chat (explanation): {e}")
            traceback.print_exc()
            return

        # 6. Generate a quiz
        print("\n--- Generating quiz (testing mode) ---")
        quiz_request_data = {
            "topic": "AI Concepts",
            "quiz_type": "multiple_choice",
            "num_questions": 3,
            "difficulty": "easy",
            "attached_files": [uploaded_filename],
            "language": "en"
        }
        try:
            response = await client.post(f"{API_BASE_URL}/quizzes/generate", headers=headers, json=quiz_request_data)
            print(f"DEBUG: Quiz generation response status: {response.status_code}")
            print(f"DEBUG: Quiz generation response text: {response.text}")
            response.raise_for_status()
            quiz_data = response.json()
            print(f"Quiz generated: {quiz_data['title']}, Questions: {len(quiz_data['questions'])}")
            if quiz_data['questions']:
                print(f"First question: {quiz_data['questions'][0]['question_text']}")
        except httpx.HTTPStatusError as e:
            print(f"Error generating quiz: {e.response.status_code} - {e.response.text}")
            return
        except Exception as e:
            import traceback
            print(f"An unexpected error occurred during quiz generation: {e}")
            traceback.print_exc()
            return

        # 7. Submit the generated quiz
        print("\n--- Submitting quiz ---")
        if not quiz_data or not quiz_data['questions']:
            print("Skipping quiz submission: No quiz data or questions generated.")
            return

        quiz_id = quiz_data['id']
        answers_to_submit = []
        for q in quiz_data['questions']:
            # For simplicity, let's assume the first option is always correct for testing purposes
            # In a real test, you'd parse the correct_answer from the quiz_data
            user_answer = q['correct_answer'] if 'correct_answer' in q else (q['options'][0] if 'options' in q and q['options'] else "N/A")
            answers_to_submit.append({
                "question_id": q['id'],
                "user_answer": user_answer
            })

        submit_quiz_data = {
            "quiz_id": quiz_id,
            "answers": answers_to_submit
        }
        try:
            response = await client.post(f"{API_BASE_URL}/quizzes/submit", headers=headers, json=submit_quiz_data)
            print(f"DEBUG: Quiz submission response status: {response.status_code}")
            print(f"DEBUG: Quiz submission raw response text: {response.text}")
            response.raise_for_status()
            quiz_result = response.json()
            print(f"Quiz submitted. Score: {quiz_result['score']}/{quiz_result['total_questions']}")
            assert quiz_result['score'] == quiz_result['total_questions'] # Assuming all answers are correct for this test
        except httpx.HTTPStatusError as e:
            print(f"Error submitting quiz: {e.response.status_code} - {e.response.text}")
            return
        except json.JSONDecodeError as e:
            print(f"JSON decoding error for quiz submission: {e}")
            print(f"Problematic response text: {response.text}")
            return
        except Exception as e:
            import traceback
            print(f"An unexpected error occurred during quiz submission: {e}")
            traceback.print_exc()
            return

        # 8. Verify quiz results are saved in user profile
        print("\n--- Verifying quiz results in profile ---")
        try:
            response = await client.get(f"{API_BASE_URL}/quiz-results/history", headers=headers)
            response.raise_for_status()
            quiz_history = response.json()
            print(f"Quiz history: {quiz_history}")
            assert any(result['quiz_id'] == quiz_id for result in quiz_history)
        except httpx.HTTPStatusError as e:
            print(f"Error fetching quiz history: {e.response.status_code} - {e.response.text}")
            return
        except Exception as e:
            import traceback
            print(f"An unexpected error occurred fetching quiz history: {e}")
            traceback.print_exc()
            return

        # 9. Send a "find what I need" message (explanation mode)
        print("\n--- Sending 'Enola, find what I need' message ---")
        find_message_data = {
            "message": "Enola, find what I need about Machine Learning in ai_concepts.md",
            "mode": "explanation",
            "tutor": "enola",
            "chat_id": chat_id,
            "attached_files": [uploaded_filename],
            "language": "en",
            "find_what_i_need": True
        }
        try:
            response = await client.post(f"{API_BASE_URL}/simple-chat", headers=headers, json=find_message_data)
            print(f"DEBUG: Find what I need response status: {response.status_code}")
            print(f"DEBUG: Find what I need raw response text: {response.text}")
            response.raise_for_status()
            find_response = response.json()
            print(f"Find what I need response: {find_response['response'][:200]}...")
            assert "Machine Learning" in find_response['response']
            assert "ai_concepts.md" in find_response['response']
        except httpx.HTTPStatusError as e:
            print(f"Error in 'find what I need' chat: {e.response.status_code} - {e.response.text}")
            return
        except json.JSONDecodeError as e:
            print(f"JSON decoding error for 'find what I need' chat: {e}")
            print(f"Problematic response text: {response.text}")
            return
        except Exception as e:
            import traceback
            print(f"An unexpected error occurred during 'find what I need' chat: {e}")
            traceback.print_exc()
            return

    print("\nBackend tests completed successfully!")

if __name__ == "__main__":
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY environment variable is not set. Please set it before running tests.")
    else:
        asyncio.run(run_backend_tests())
