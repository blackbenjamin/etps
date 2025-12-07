import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'backend'))

from backend.db.database import SessionLocal
from backend.db.models import User

def update_user_profile():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == 1).first()
        if not user:
            print("User 1 not found!")
            return

        print(f"Updating user: {user.full_name}")
        print(f"Old Email: {user.email}")
        
        # Check for conflict
        target_email = "ben@benjaminblack.consulting"
        existing_user = db.query(User).filter(User.email == target_email).first()
        if existing_user and existing_user.id != 1:
            print(f"Found conflicting user {existing_user.id} with email {target_email}. Deleting related records...")
            
            # Delete related records manually to avoid FK constraints if cascade fails
            from backend.db.models import Template, Experience, Bullet, Application, Contact, LogEntry, JobProfile, CriticLog, ApprovedOutput
            
            # Delete in order of dependency (children first)
            db.query(LogEntry).filter(LogEntry.user_id == existing_user.id).delete()
            db.query(CriticLog).filter(CriticLog.user_id == existing_user.id).delete()
            db.query(ApprovedOutput).filter(ApprovedOutput.user_id == existing_user.id).delete()
            db.query(Contact).filter(Contact.user_id == existing_user.id).delete()
            db.query(Application).filter(Application.user_id == existing_user.id).delete()
            db.query(Bullet).filter(Bullet.user_id == existing_user.id).delete()
            db.query(Experience).filter(Experience.user_id == existing_user.id).delete()
            db.query(Template).filter(Template.user_id == existing_user.id).delete()
            db.query(JobProfile).filter(JobProfile.user_id == existing_user.id).delete()
            
            print("Deleting user...")
            db.delete(existing_user)
            db.commit()
        
        # Update fields
        user.email = target_email
        user.phone = "617-504-5529"
        user.linkedin_url = "linkedin.com/in/benjaminblack"
        
        # Note: User model might not have portfolio_url field yet based on schema review
        # Checking backend/db/models.py would confirm, but let's try to set it if it exists
        if hasattr(user, 'portfolio_url'):
            user.portfolio_url = "benjaminblack.consulting/projects"
            print("Updated portfolio_url")
        else:
            print("User model does not have portfolio_url field. Skipping.")

        db.commit()
        db.refresh(user)
        
        print("Update successful!")
        print(f"New Email: {user.email}")
        print(f"New Phone: {user.phone}")
        
    except Exception as e:
        print(f"Error updating user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_user_profile()
