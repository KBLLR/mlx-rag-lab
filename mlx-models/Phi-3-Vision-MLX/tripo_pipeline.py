import requests
import time
import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Access the API key
API_KEY = os.getenv("TRIPO_API_KEY")

if not API_KEY:
    raise ValueError("TRIPO_API_KEY not set in the .env file.")

# Base URL
BASE_URL = "https://api.tripo3d.ai/v2/openapi"

# Local URL
file_path = "assets/uploads/tai-001.png"

# Get User Balance
def get_user_balance(API_KEY):
    url = f"{BASE_URL}/user/balance"
    headers = {"Authorization": f"Bearer {API_KEY}"}

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error fetching balance: {response.json()}")

# Upload File
def upload_file(api_key, file_path):
    url = f"{BASE_URL}/upload"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    files = {"file": open(file_path, "rb")}

    response = requests.post(url, headers=headers, files=files)
    if response.status_code == 200:
        return response.json()["data"]["image_token"]
    else:
        raise Exception(f"Error uploading file: {response.json()}")

# Create Task
def create_task(api_key, prompt=None, image_token=None):
    url = f"{BASE_URL}/task"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

    if image_token:
        # Image-to-Model Task
        payload = {
            "type": "image_to_model",
            "file": {"type": "image", "file_token": image_token},
            "model_version": "default",
            "texture": True,
            "pbr": True
        }
    elif prompt:
        # Text-to-Model Task
        payload = {
            "type": "text_to_model",
            "prompt": prompt,
            "model_version": "default",
            "texture": True,
            "pbr": True
        }
    else:
        raise ValueError("Either prompt or image_token must be provided.")

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()["data"]["task_id"]
    else:
        raise Exception(f"Error creating task: {response.json()}")

# Get Task Status
def get_task_status(api_key, task_id):
    url = f"{BASE_URL}/task/{task_id}"
    headers = {"Authorization": f"Bearer {API_KEY}"}

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error fetching task status: {response.json()}")

# Main Workflow
def main():
    # Replace this with your API key
    api_key = "your_api_key_here"

    try:
        # Step 1: Get user balance
        print("Checking user balance...")
        balance = get_user_balance(api_key)
        print(f"Balance: {balance['data']['balance']}, Frozen: {balance['data']['frozen']}")

        # Step 2: Upload file (if image-based task)
        file_path = "path/to/your/image.png"
        print("Uploading file...")
        image_token = upload_file(api_key, file_path)
        print(f"Image token: {image_token}")

        # Step 3: Create a task (choose either image-based or text-based)
        prompt = "A futuristic 3D model of a robotic arm."
        print("Creating a task...")
        task_id = create_task(api_key, prompt=prompt, image_token=image_token)
        print(f"Task ID: {task_id}")

        # Step 4: Check task status
        print("Checking task status...")
        while True:
            status = get_task_status(api_key, task_id)
            task_status = status["data"]["status"]
            print(f"Task Status: {task_status}")
            if task_status in ["success", "failed"]:
                break
            time.sleep(5)  # Wait before retrying

        # Step 5: Handle task result
        if task_status == "success":
            output = status["data"]["output"]
            print("Task completed successfully!")
            print(f"Output Model: {output['model']}")
            print(f"Rendered Image: {output['rendered_image']}")
        else:
            print(f"Task failed: {status['data'].get('message', 'No additional details provided.')}")

    except Exception as e:
        print(f"An error occurred: {e}")

# Run the main workflow
if __name__ == "__main__":
    main()
