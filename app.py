from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import google.generativeai as genai
from github import Github
import os
import logging
from concurrent.futures import ThreadPoolExecutor
import asyncio
from functools import lru_cache
import hashlib
from datetime import datetime, timedelta
import json
from dotenv import load_dotenv
    

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
    }
})

# Configure logging
logging.basicConfig(level=logging.DEBUG)
load_dotenv()
# Configure Gemini and GitHub API keys
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
github = Github(os.getenv('GITHUB_API_KEY'))

cache = {}

def get_cache_key(repo_name):
    return hashlib.md5(repo_name.encode()).hexdigest()

@lru_cache(maxsize=100)
def get_cached_readme(cache_key):
    if cache_key in cache:
        data = cache[cache_key]
        if datetime.now() - data['timestamp'] < timedelta(hours=24):
            return data['readme']
    return None

def update_cache(cache_key, readme):
    cache[cache_key] = {
        'readme': readme,
        'timestamp': datetime.now()
    }

@app.route('/generate-readme', methods=['POST'])
def api_generate_readme():
    try:
        data = request.get_json()
        repo_name = data.get('repo_name')
        
        if not repo_name:
            return jsonify({"error": "Repository name is required"}), 400

        app.logger.info(f"Received request for repo: {repo_name}")

        try:
            repo = github.get_repo(repo_name)
            app.logger.info(f"Successfully accessed repository: {repo_name}")
        except Exception as e:
            app.logger.error(f"Error accessing repository: {str(e)}")
            return jsonify({"error": f"Error accessing repository: {str(e)}"}), 404

        try:
            readme_content = generate_readme(repo)
            app.logger.info("README generated successfully")
            return jsonify({"readme": readme_content})
        except Exception as e:
            app.logger.error(f"Error generating README: {str(e)}")
            return jsonify({"error": f"Error generating README: {str(e)}"}), 500

    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

def generate_readme(repo):
    app.logger.info("Starting README generation")
    
    # Fetch repo code
    files = get_repo_files_and_code(repo)
    app.logger.info(f"Fetched {len(files)} files from the repository")

    # Prepare prompt
    prompt = prepare_prompt(files)
    app.logger.info("Prepared prompt for Gemini")

    # Generate README content using Gemini
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    app.logger.info("Received response from Gemini")

    return response.text

def get_repo_files_and_code(repo):
    files = []
    skipped_files = []
    
    def process_content(content):
        if content.type == "dir":
            contents = repo.get_contents(content.path)
            for sub_content in contents:
                process_content(sub_content)
        elif content.path.lower() not in ['readme.md', 'requirements.txt', '.gitignore']:
            try:
                if content.encoding == "base64":
                    file_content = content.decoded_content.decode("utf-8")
                    files.append({"path": content.path, "content": file_content})
            except (UnicodeDecodeError, IOError):
                skipped_files.append(content.path)

    with ThreadPoolExecutor(max_workers=10) as executor:
        contents = repo.get_contents("")
        executor.map(process_content, contents)
    
    app.logger.info(f"Skipped files due to decoding issues: {skipped_files}")
    return files

def prepare_prompt(files):
    # Limit total files processed
    MAX_FILES = 8
    MAX_CONTENT_LENGTH = 500  # characters per file
    
    prompt = (
        "Generate a structured README for a GitHub repository based on its files and structure.\n\n"
        "Structure:\n"
        "1. **Overview** - Brief introduction to the project and its purpose.\n"
        "2. **Project Structure** - Show the structure of the Repository.\n"
        "3. **Installation** - Installation instructions if any dependencies are detected.\n"
        "4. **Usage** - Describe how to use the application.\n"
        "5. **API Endpoints** (if applicable) - List of key API endpoints if it's a backend or API project.\n"
        "6. **Data Models or Machine Learning Models** - Overview of any models used if it's a data science project.\n"
        "7. **Contributing** - Standard contributing section.\n"
        "8. **License** - Placeholder for license details.\n"
        "9. **Contact** - How to reach out for questions or feedback.\n"
        "10. **Acknowledgements** - List of libraries or tools used in the project.\n\n"
        "Here is the code structure and initial content:\n\n"
    )

    # Prioritize important files
    main_files = [f for f in files if any(key in f['path'].lower() 
                 for key in ['main', 'app', 'index', 'config'])][:3]
    other_files = [f for f in files if f not in main_files]
    selected_files = main_files + other_files[:MAX_FILES - len(main_files)]

    # Add file structure overview
    prompt += "Repository Structure:\n"
    for file in files:
        prompt += f"- {file['path']}\n"
    prompt += "\nKey File Contents:\n\n"

    for file in selected_files:
        prompt += f"File: {file['path']}\n"
        content_preview = file['content'][:MAX_CONTENT_LENGTH]
        prompt += f"Content: {content_preview}\n\n"

    return prompt

@app.route('/generate-readme-progress', methods=['GET'])
def api_generate_readme_with_progress():
    def generate():
        repo_name = request.args.get('repo_name')
        
        if not repo_name:
            yield "data: " + json.dumps({"status": "error", "error": "Repository name is required"}) + "\n\n"
            return

        yield "data: " + json.dumps({"status": "started", "progress": 0}) + "\n\n"
        
        try:
            repo = github.get_repo(repo_name)
            yield "data: " + json.dumps({"status": "repo_accessed", "progress": 20}) + "\n\n"
            
            files = get_repo_files_and_code(repo)
            yield "data: " + json.dumps({"status": "files_fetched", "progress": 50}) + "\n\n"
            
            prompt = prepare_prompt(files)
            yield "data: " + json.dumps({"status": "prompt_prepared", "progress": 70}) + "\n\n"
            
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            
            yield "data: " + json.dumps({
                "status": "completed",
                "progress": 100,
                "readme": response.text
            }) + "\n\n"
            
        except Exception as e:
            yield "data: " + json.dumps({"status": "error", "error": str(e)}) + "\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)