"""LLM-assisted application generator."""

import os
import base64
import json
from datetime import datetime
from openai import OpenAI
from github_handler import create_repo, push_to_repo, enable_github_pages
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


def decode_attachments(attachments):
    """Decode base64 attachments from data URIs."""
    decoded = []
    
    for attachment in attachments:
        name = attachment.get('name', 'file')
        url = attachment.get('url', '')
        
        if url.startswith('data:'):
            # Parse data URI: data:mime/type;base64,encoded_data
            parts = url.split(',', 1)
            if len(parts) == 2:
                mime_info = parts[0].split(';')[0].replace('data:', '')
                encoding = 'base64' if ';base64' in parts[0] else 'text'
                
                if encoding == 'base64':
                    content = base64.b64decode(parts[1]).decode('utf-8', errors='ignore')
                else:
                    content = parts[1]
                
                decoded.append({
                    'name': name,
                    'content': content,
                    'mime': mime_info
                })
    
    return decoded


def generate_app_code(brief, checks, attachments):
    """Use OpenAI to generate app code based on brief and requirements."""
    
    # Decode attachments
    decoded_attachments = decode_attachments(attachments)
    
    # Prepare attachment information for the prompt
    attachment_info = ""
    if decoded_attachments:
        attachment_info = "\n\nAttachments provided:\n"
        for att in decoded_attachments:
            attachment_info += f"- {att['name']} ({att['mime']})\n"
            attachment_info += f"  Content preview: {att['content'][:200]}...\n"
    
    # Prepare checks information
    checks_info = "\n\nChecks that will be run:\n"
    for check in checks:
        checks_info += f"- {check}\n"
    
    system_prompt = """You are an expert web developer. Generate a complete, production-ready single-page web application based on the requirements.

Requirements:
1. Create a single HTML file (index.html) that is self-contained
2. Use modern JavaScript (ES6+) and best practices
3. Include all CSS inline or use CDN links for frameworks
4. Use CDN links for any required libraries (Bootstrap, jQuery, marked.js, highlight.js, etc.)
5. Ensure the app is fully functional and meets all specified checks
6. Add proper error handling and user feedback
7. Make the UI clean, professional, and responsive
8. Include comments explaining key sections

Return ONLY a JSON object with this structure:
{
  "index.html": "full HTML content here",
  "README.md": "comprehensive README with setup, usage, and explanation"
}

Do not include any other text or explanation outside the JSON."""

    user_prompt = f"""Brief: {brief}

{checks_info}
{attachment_info}

Generate a complete web application that satisfies all requirements and checks."""

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=4000,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return result, decoded_attachments
        
    except Exception as e:
        print(f"Error generating app with OpenAI: {str(e)}")
        # Fallback to basic template
        return generate_fallback_app(brief, checks, decoded_attachments), decoded_attachments


def generate_fallback_app(brief, checks, attachments):
    """Generate a basic fallback app if LLM fails."""
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated App</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{
            padding: 2rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            background: white;
            border-radius: 10px;
            padding: 2rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1 class="mb-4">Generated Application</h1>
        <div class="alert alert-info">
            <h5>Brief:</h5>
            <p>{brief}</p>
        </div>
        <div id="app-content">
            <p>Loading...</p>
        </div>
    </div>
    <script>
        // Application logic here
        console.log('App initialized');
    </script>
</body>
</html>"""

    readme_content = f"""# Generated Application

## Overview
This application was automatically generated based on the following brief:

{brief}

## Features
- Single-page web application
- Bootstrap 5 UI
- Responsive design

## Usage
Open `index.html` in a web browser or visit the GitHub Pages URL.

## Checks
The following checks will be validated:
{chr(10).join([f"- {check}" for check in checks])}

## License
MIT License
"""

    return {
        "index.html": html_content,
        "README.md": readme_content
    }


def generate_and_deploy_app(request_data):
    """
    Main function to generate app and deploy to GitHub.
    
    Args:
        request_data: Dict containing task request details
        
    Returns:
        Dict with repo_url, commit_sha, pages_url
    """
    print(f"[{datetime.utcnow().isoformat()}] Starting app generation...")
    
    # Generate app code using LLM
    generated_files, attachments = generate_app_code(
        brief=request_data['brief'],
        checks=request_data['checks'],
        attachments=request_data.get('attachments', [])
    )
    
    print(f"[{datetime.utcnow().isoformat()}] App code generated")
    
    # Prepare files for GitHub
    files = {
        'index.html': generated_files.get('index.html', ''),
        'README.md': generated_files.get('README.md', ''),
        'LICENSE': get_mit_license()
    }
    
    # Add attachment files
    for att in attachments:
        files[att['name']] = att['content']
    
    # Create unique repo name based on task
    repo_name = request_data['task'].replace(' ', '-').lower()
    
    print(f"[{datetime.utcnow().isoformat()}] Creating GitHub repo: {repo_name}")
    
    # Create repo and push
    repo = create_repo(repo_name, f"Generated app for {request_data['task']}")
    commit_sha = push_to_repo(repo, files)
    
    print(f"[{datetime.utcnow().isoformat()}] Pushed to repo, commit: {commit_sha}")
    
    # Enable GitHub Pages
    pages_url = enable_github_pages(repo)
    
    print(f"[{datetime.utcnow().isoformat()}] GitHub Pages enabled: {pages_url}")
    
    return {
        'repo_url': repo.html_url,
        'commit_sha': commit_sha,
        'pages_url': pages_url
    }


def get_mit_license():
    """Return MIT license text."""
    year = datetime.now().year
    return f"""MIT License

Copyright (c) {year}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
