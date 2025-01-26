from flask import Flask, render_template, request, Response, stream_with_context, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

import webbrowser
from threading import Timer
import os
import requests

app = Flask(__name__)

CORS(app)  # Enable CORS for all routes

# Load environment variables
load_dotenv()

fastapi_llm_url = "http://model:8000/call_llm/"

@app.route('/')
def index():
    return render_template('/index.html')
    
@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    
    def generate():
        try:
            with requests.post(
                fastapi_llm_url,
                params={"prompt": user_message},
                stream=True
            ) as response:
                response.raise_for_status()
                for chunk in response.iter_content(chunk_size=None):
                    if chunk:
                        yield chunk.decode()
        except Exception as e:
            yield f"Erreur : {str(e)}"

    return Response(stream_with_context(generate()), content_type='text/plain')

@app.route('/get_llm_list', methods=['GET'])
def get_llm_list():
    try:
        response = requests.get("http://model:8000/llm_list")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to retrieve LLM list: {str(e)}"}, 500


def call_custom_llm(prompt: str) -> str:
    try:
        response = requests.post(fastapi_llm_url+"?prompt="+prompt)
        response.raise_for_status()
        return response.json().get("response", "")
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Failed to call custom LLM: {str(e)}")

def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000/')
    
@app.route('/get_readme_files', methods=['GET'])
def get_readme_files():
    try:
        # Example: Fetch README files from a directory
        readme_files = []
        readme_dir = os.path.join(os.path.dirname(__file__), 'readme_files')
        for filename in os.listdir(readme_dir):
            if filename.endswith('.md'):
                with open(os.path.join(readme_dir, filename), 'r') as file:
                    content = file.read()
                    readme_files.append({
                        'name': filename,
                        'content': content
                    })
        return jsonify({'readmeFiles': readme_files})
    except Exception as e:
        return jsonify({'error': f"Failed to retrieve README files: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)