"""Script to send round 2 tasks to students."""

import requests
from datetime import datetime
from uuid_extensions import uuid7str
from database import get_session, Task, Repo
from task_templates import get_task_templates, generate_task_data
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()


def generate_task_id(template_id, brief, attachments):
    """Generate unique task ID based on template and content."""
    content = f"{brief}{str(attachments)}"
    hash_val = hashlib.sha256(content.encode()).hexdigest()[:5]
    return f"{template_id}-{hash_val}"


def send_task(endpoint, email, secret, task_data, evaluation_url):
    """
    Send round 2 task to student endpoint.
    
    Args:
        endpoint: Student API endpoint
        email: Student email
        secret: Student secret
        task_data: Dict with task details
        evaluation_url: URL for evaluation API
        
    Returns:
        HTTP status code
    """
    payload = {
        "email": email,
        "secret": secret,
        "task": task_data['task_id'],
        "round": 2,
        "nonce": task_data['nonce'],
        "brief": task_data['brief'],
        "checks": task_data['checks'],
        "evaluation_url": evaluation_url,
        "attachments": task_data.get('attachments', [])
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print(f"[{datetime.utcnow().isoformat()}] Sending round 2 task to {email}...")
        
        response = requests.post(
            endpoint,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        print(f"[{datetime.utcnow().isoformat()}] Response: {response.status_code}")
        
        return response.status_code
        
    except requests.exceptions.RequestException as e:
        print(f"[{datetime.utcnow().isoformat()}] Request failed: {str(e)}")
        return 0


def run_round2():
    """
    Main function to run round 2 task distribution.
    
    Sends round 2 tasks to students who completed round 1.
    """
    print(f"[{datetime.utcnow().isoformat()}] Starting Round 2 task distribution...")
    
    session = get_session()
    
    try:
        # Get all round 1 repos (students who submitted)
        round1_repos = session.query(Repo).filter_by(round=1).all()
        
        print(f"[{datetime.utcnow().isoformat()}] Found {len(round1_repos)} round 1 submissions")
        
        # Load task templates
        templates = get_task_templates()
        
        # Get evaluation URL
        evaluation_url = os.getenv('API_BASE_URL', 'http://localhost:5001') + '/api/submit'
        
        for repo in round1_repos:
            email = repo.email
            
            # Check if round 2 task already sent
            existing_round2 = session.query(Task).filter_by(
                email=email,
                round=2
            ).first()
            
            if existing_round2:
                print(f"[{datetime.utcnow().isoformat()}] Skipping {email} - already sent round 2")
                continue
            
            # Get original round 1 task to find the template
            round1_task = session.query(Task).filter_by(
                email=email,
                task=repo.task,
                round=1
            ).first()
            
            if not round1_task:
                print(f"[{datetime.utcnow().isoformat()}] Warning: No round 1 task found for {email}")
                continue
            
            # Get the endpoint and secret from round 1
            endpoint = round1_task.endpoint
            secret = round1_task.secret
            
            # Generate round 2 task using same seed/template family
            seed = f"{email}:{datetime.utcnow().strftime('%Y-%m-%d-%H')}"
            
            task_data = generate_task_data(templates, seed, round_num=2)
            
            # Generate task ID
            task_id = generate_task_id(
                task_data['template_id'],
                task_data['brief'],
                task_data.get('attachments', [])
            )
            
            # Generate nonce
            nonce = uuid7str()
            
            task_data['task_id'] = task_id
            task_data['nonce'] = nonce
            
            # Send task to student
            status_code = send_task(endpoint, email, secret, task_data, evaluation_url)
            
            # Log to database
            task = Task(
                email=email,
                task=task_id,
                round=2,
                nonce=nonce,
                brief=task_data['brief'],
                attachments=task_data.get('attachments', []),
                checks=task_data['checks'],
                evaluation_url=evaluation_url,
                endpoint=endpoint,
                statuscode=status_code,
                secret=secret
            )
            
            session.add(task)
            session.commit()
            
            print(f"[{datetime.utcnow().isoformat()}] Round 2 task logged for {email}")
        
        print(f"[{datetime.utcnow().isoformat()}] Round 2 distribution complete!")
        
    finally:
        session.close()


if __name__ == '__main__':
    run_round2()
