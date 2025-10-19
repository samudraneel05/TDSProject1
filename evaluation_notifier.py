"""Module for notifying evaluation API with exponential backoff."""

import requests
import time
from datetime import datetime


def notify_evaluation(evaluation_url, email, task, round_num, nonce, repo_url, commit_sha, pages_url, max_retries=5):
    """
    Notify evaluation API with repo details using exponential backoff.
    
    Args:
        evaluation_url: URL to POST results to
        email: Student email
        task: Task ID
        round_num: Round number
        nonce: Request nonce
        repo_url: GitHub repository URL
        commit_sha: Commit SHA
        pages_url: GitHub Pages URL
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dict with status and response
    """
    payload = {
        "email": email,
        "task": task,
        "round": round_num,
        "nonce": nonce,
        "repo_url": repo_url,
        "commit_sha": commit_sha,
        "pages_url": pages_url
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    for attempt in range(max_retries):
        try:
            print(f"[{datetime.utcnow().isoformat()}] Notifying evaluation API (attempt {attempt + 1}/{max_retries})...")
            
            response = requests.post(
                evaluation_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"[{datetime.utcnow().isoformat()}] Successfully notified evaluation API")
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "response": response.text,
                    "attempt": attempt + 1
                }
            else:
                print(f"[{datetime.utcnow().isoformat()}] Received status {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"[{datetime.utcnow().isoformat()}] Request failed: {str(e)}")
        
        # Exponential backoff: 1, 2, 4, 8 seconds
        if attempt < max_retries - 1:
            delay = 2 ** attempt
            print(f"[{datetime.utcnow().isoformat()}] Retrying in {delay} seconds...")
            time.sleep(delay)
    
    print(f"[{datetime.utcnow().isoformat()}] Failed to notify evaluation API after {max_retries} attempts")
    return {
        "success": False,
        "attempts": max_retries
    }
