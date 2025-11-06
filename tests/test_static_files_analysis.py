import httpx
import asyncio
import os
import json
from pathlib import Path
import time

# Ensure the API key is loaded from .env for this script
from dotenv import load_dotenv
load_dotenv()

API_BASE_URL = "http://localhost:8002"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

async def run_static_files_analysis_test():
    print("Starting static files analysis test...")

    # Start the FastAPI application in a subprocess
    # This assumes 'make run' starts the server and keeps it running
    # For a proper integration test, you might want to start/stop the server programmatically
    # or use FastAPI's TestClient with a mocked database.
    # For this scenario, we'll assume the user has started the server with 'make run'
    # and we are just interacting with it.

    async with httpx.AsyncClient() as client:
        # 1. Register a new user
        print("\n--- Registering new user ---")
        register_data = {
            "email": "static_testuser@example.com",
            "username": "static_testuser",
            "password": "static_testpassword"
        }
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
            "email": "static_testuser@example.com",
            "password": "static_testpassword"
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

        # 4. Upload all files from the static/ directory
        print("\n--- Uploading static/ files ---")
        static_dir = Path("static/")
        uploaded_filenames = []
        for file_path in static_dir.iterdir():
            if file_path.is_file():
                print(f"Uploading {file_path.name}...")
                try:
                    with open(file_path, "rb") as f:
                        files = {"file": (file_path.name, f, "application/octet-stream")}
                        response = await client.post(f"{API_BASE_URL}/documents/upload", headers=headers, files=files)
                        response.raise_for_status()
                        upload_info = response.json()
                        print(f"File uploaded: {upload_info['filename']} - {upload_info.get('message', 'Success')}")
                        uploaded_filenames.append(upload_info["filename"])
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 400 and "File already exists" in e.response.text:
                        print(f"File {file_path.name} already exists, skipping upload.")
                        uploaded_filenames.append(file_path.name) # Add to list even if existing
                    else:
                        print(f"Error uploading {file_path.name}: {e.response.status_code} - {e.response.text}")
                        return
                except Exception as e:
                    import traceback
                    print(f"An unexpected error occurred during upload of {file_path.name}: {e}")
                    traceback.print_exc()
                    return
        print(f"All static files uploaded. Total: {len(uploaded_filenames)}")

        # 5. Ask Enola to analyze the uploaded files for authentication code
        print("\n--- Asking Enola to analyze for authentication code ---")
        analysis_message = "Enola, find what I need about authentication code in the uploaded files. Outline in which file the information is found."
        analysis_data = {
            "message": analysis_message,
            "mode": "explanation",
            "tutor": "enola",
            "chat_id": chat_id,
            "attached_files": uploaded_filenames,
            "language": "en",
            "find_what_i_need": True
        }
        
        # Due to potential LLM rate limits, add a retry mechanism or delay
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = await client.post(f"{API_BASE_URL}/simple-chat", headers=headers, json=analysis_data)
                print(f"DEBUG: Enola analysis response status: {response.status_code}")
                print(f"DEBUG: Enola analysis raw response text: {response.text}")
                response.raise_for_status()
                analysis_response = response.json()
                print(f"Enola's analysis: {analysis_response['response'][:500]}...")
                
                # Assertions to check if Enola identified relevant files
                assert "authentication" in analysis_response['response'].lower()
                assert "auth.html" in analysis_response['response'].lower() or "api.js" in analysis_response['response'].lower() or "app.js" in analysis_response['response'].lower()
                print("\nStatic files analysis test completed successfully!")
                return # Exit on success
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429 and attempt < max_retries - 1:
                    retry_after = int(e.response.headers.get("Retry-After", 60))
                    print(f"Rate limit hit. Retrying in {retry_after} seconds (Attempt {attempt + 1}/{max_retries})...")
                    time.sleep(retry_after + 5) # Add a small buffer
                else:
                    print(f"Error in Enola analysis: {e.response.status_code} - {e.response.text}")
                    return
            except json.JSONDecodeError as e:
                print(f"JSON decoding error for Enola analysis: {e}")
                print(f"Problematic response text: {response.text}")
                return
            except Exception as e:
                import traceback
                print(f"An unexpected error occurred during Enola analysis: {e}")
                traceback.print_exc()
                return
        
        print("\nStatic files analysis test failed after multiple retries due to rate limits or other errors.")


if __name__ == "__main__":
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY environment variable is not set. Please set it before running tests.")
    else:
        asyncio.run(run_static_files_analysis_test())
