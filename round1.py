"""Script to send round 1 tasks to students."""

import csv
import hashlib
import base64
import requests
import yaml
from datetime import datetime
from uuid_extensions import uuid7str
from database import get_session, Task
from task_templates import get_task_templates, generate_task_data
import os
from dotenv import load_dotenv

load_dotenv()


def load_submissions(csv_path='submissions.csv'):
    """
    Load submissions from CSV file.
    
    Expected columns: timestamp, email, endpoint, secret
    """
    submissions = []
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            submissions.append({
                'timestamp': row['timestamp'],
                'email': row['email'],
                'endpoint': row['endpoint'],
                'secret': row['secret']
            })
    
    return submissions


def generate_task_id(template_id, brief, attachments):
    """Generate unique task ID based on template and content."""
    content = f"{brief}{str(attachments)}"
    hash_val = hashlib.sha256(content.encode()).hexdigest()[:5]
    return f"{template_id}-{hash_val}"


def send_task(submission, task_data, evaluation_url):
    """
    Send task to student endpoint.
    
    Args:
        submission: Dict with student info
        task_data: Dict with task details
        evaluation_url: URL for evaluation API
        
    Returns:
        HTTP status code
    """
    payload = {
        "email": submission['email'],
        "secret": submission['secret'],
        "task": task_data['task_id'],
        "round": 1,
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
        print(f"[{datetime.utcnow().isoformat()}] Sending task to {submission['email']}...")
        
        response = requests.post(
            submission['endpoint'],
            json=payload,
            headers=headers,
            timeout=30
        )
        
        print(f"[{datetime.utcnow().isoformat()}] Response: {response.status_code}")
        
        return response.status_code
        
    except requests.exceptions.RequestException as e:
        print(f"[{datetime.utcnow().isoformat()}] Request failed: {str(e)}")
        return 0


def run_round1(csv_path='submissions.csv'):
    """
    Main function to run round 1 task distribution.
    
    Args:
        csv_path: Path to submissions CSV
    """
    print(f"[{datetime.utcnow().isoformat()}] Starting Round 1 task distribution...")
    
    # Load submissions
    submissions = load_submissions(csv_path)
    print(f"[{datetime.utcnow().isoformat()}] Loaded {len(submissions)} submissions")
    
    # Load task templates
    templates = get_task_templates()
    print(f"[{datetime.utcnow().isoformat()}] Loaded {len(templates)} task templates")
    
    # Get evaluation URL
    evaluation_url = os.getenv('API_BASE_URL', 'http://localhost:5001') + '/api/submit'
    
    session = get_session()
    
    try:
        for submission in submissions:
            email = submission['email']
            
            # Check if already sent
            existing_task = session.query(Task).filter_by(
                email=email,
                round=1
            ).first()
            
            if existing_task:
                print(f"[{datetime.utcnow().isoformat()}] Skipping {email} - already sent round 1")
                continue
            
            # Generate task for this student
            # Use email and current date as seed for randomization
            seed = f"{email}:{datetime.utcnow().strftime('%Y-%m-%d-%H')}"
            
            task_data = generate_task_data(templates, seed, round_num=1)
            
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
            status_code = send_task(submission, task_data, evaluation_url)
            
            # Log to database
            task = Task(
                email=email,
                task=task_id,
                round=1,
                nonce=nonce,
                brief=task_data['brief'],
                attachments=task_data.get('attachments', []),
                checks=task_data['checks'],
                evaluation_url=evaluation_url,
                endpoint=submission['endpoint'],
                statuscode=status_code,
                secret=submission['secret']
            )
            
            session.add(task)
            session.commit()
            
            print(f"[{datetime.utcnow().isoformat()}] Task logged for {email}")
        
        print(f"[{datetime.utcnow().isoformat()}] Round 1 distribution complete!")
        
    finally:
        session.close()


if __name__ == '__main__':
    import sys
    
    csv_path = sys.argv[1] if len(sys.argv) > 1 else 'submissions.csv'
    run_round1(csv_path)
