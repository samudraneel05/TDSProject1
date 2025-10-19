"""Evaluation API endpoint for receiving student submissions."""

from flask import Flask, request, jsonify
from datetime import datetime
from database import get_session, Task, Repo
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat()}), 200


@app.route('/api/submit', methods=['POST'])
def submit_repo():
    """
    Endpoint for students to submit their repo details.
    
    Expected JSON:
    {
        "email": "student@example.com",
        "task": "task-id",
        "round": 1,
        "nonce": "unique-nonce",
        "repo_url": "https://github.com/user/repo",
        "commit_sha": "abc123",
        "pages_url": "https://user.github.io/repo/"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400
        
        # Validate required fields
        required_fields = ['email', 'task', 'round', 'nonce', 'repo_url', 'commit_sha', 'pages_url']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({"error": f"Missing fields: {', '.join(missing_fields)}"}), 400
        
        session = get_session()
        
        try:
            # Check if matching task exists
            task = session.query(Task).filter_by(
                email=data['email'],
                task=data['task'],
                round=data['round'],
                nonce=data['nonce']
            ).first()
            
            if not task:
                return jsonify({
                    "error": "No matching task found",
                    "details": "The provided email, task, round, and nonce do not match any sent task"
                }), 400
            
            # Check if already submitted
            existing_repo = session.query(Repo).filter_by(
                email=data['email'],
                task=data['task'],
                round=data['round'],
                nonce=data['nonce']
            ).first()
            
            if existing_repo:
                # Update existing submission
                existing_repo.repo_url = data['repo_url']
                existing_repo.commit_sha = data['commit_sha']
                existing_repo.pages_url = data['pages_url']
                existing_repo.timestamp = datetime.utcnow()
                message = "Submission updated"
            else:
                # Create new submission
                repo = Repo(
                    email=data['email'],
                    task=data['task'],
                    round=data['round'],
                    nonce=data['nonce'],
                    repo_url=data['repo_url'],
                    commit_sha=data['commit_sha'],
                    pages_url=data['pages_url']
                )
                session.add(repo)
                message = "Submission received"
            
            session.commit()
            
            print(f"[{datetime.utcnow().isoformat()}] Received submission:")
            print(f"  Email: {data['email']}")
            print(f"  Task: {data['task']}")
            print(f"  Round: {data['round']}")
            print(f"  Repo: {data['repo_url']}")
            
            return jsonify({
                "status": "success",
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            }), 200
            
        finally:
            session.close()
        
    except Exception as e:
        print(f"[{datetime.utcnow().isoformat()}] Error processing submission: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/submissions', methods=['GET'])
def list_submissions():
    """List all submissions (for instructors)."""
    try:
        session = get_session()
        
        try:
            repos = session.query(Repo).order_by(Repo.timestamp.desc()).all()
            
            submissions = []
            for repo in repos:
                submissions.append({
                    "id": repo.id,
                    "timestamp": repo.timestamp.isoformat(),
                    "email": repo.email,
                    "task": repo.task,
                    "round": repo.round,
                    "repo_url": repo.repo_url,
                    "commit_sha": repo.commit_sha,
                    "pages_url": repo.pages_url
                })
            
            return jsonify({
                "count": len(submissions),
                "submissions": submissions
            }), 200
            
        finally:
            session.close()
        
    except Exception as e:
        print(f"[{datetime.utcnow().isoformat()}] Error listing submissions: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    port = int(os.getenv('EVALUATION_PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=os.getenv('FLASK_ENV') == 'development')
