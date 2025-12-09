import sys
import os
import json
from dotenv import load_dotenv

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'backend'))

# Load environment variables from backend/.env
load_dotenv(os.path.join(project_root, 'backend', '.env'))

from backend.db.database import SessionLocal
from backend.db.models import User

def inspect_user():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == 1).first()
        if not user:
            print("User 1 not found")
            return
        
        print(f"User: {user.full_name}")
        print("Candidate Profile:")
        if user.candidate_profile:
            print(json.dumps(user.candidate_profile, indent=2))
        else:
            print("None")
            
    finally:
        db.close()

if __name__ == "__main__":
    inspect_user()
