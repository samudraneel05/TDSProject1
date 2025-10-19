"""Main Flask API application for student endpoint."""

from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from datetime import datetime
import traceback
from app_generator import generate_and_deploy_app
from evaluation_notifier import notify_evaluation

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')

# Store for student secret (in production, use database)
STUDENT_SECRET = os.getenv('STUDENT_SECRET', '')


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat()}), 200


@app.route('/api/build', methods=['POST'])
def build_endpoint():
    """
    Main API endpoint for receiving build/revision requests.
    Accepts JSON POST with task details and generates/deploys app.
    """
    try:
        # Parse request
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400
        
        # Validate required fields
        required_fields = ['email', 'secret', 'task', 'round', 'nonce', 'brief', 'checks', 'evaluation_url']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({"error": f"Missing fields: {', '.join(missing_fields)}"}), 400
        
        # Verify secret
        if data['secret'] != STUDENT_SECRET:
            return jsonify({"error": "Invalid secret"}), 403
        
        # Log request
        print(f"[{datetime.utcnow().isoformat()}] Received request:")
        print(f"  Email: {data['email']}")
        print(f"  Task: {data['task']}")
        print(f"  Round: {data['round']}")
        print(f"  Brief: {data['brief'][:100]}...")
        
        # Send immediate 200 response
        response = jsonify({
            "status": "received",
            "message": "Request accepted and processing",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Process asynchronously (in production, use Celery/background worker)
        # For now, we'll process synchronously with a timeout
        try:
            result = generate_and_deploy_app(data)
            
            # Notify evaluation API
            notify_result = notify_evaluation(
                evaluation_url=data['evaluation_url'],
                email=data['email'],
                task=data['task'],
                round_num=data['round'],
                nonce=data['nonce'],
                repo_url=result['repo_url'],
                commit_sha=result['commit_sha'],
                pages_url=result['pages_url']
            )
            
            print(f"[{datetime.utcnow().isoformat()}] Notification result: {notify_result}")
            
        except Exception as e:
            print(f"[{datetime.utcnow().isoformat()}] Error processing request: {str(e)}")
            print(traceback.format_exc())
        
        return response, 200
        
    except Exception as e:
        print(f"[{datetime.utcnow().isoformat()}] Unexpected error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.getenv('FLASK_ENV') == 'development')
