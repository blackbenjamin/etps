import sys
import os
import json
import pandas as pd
from dotenv import load_dotenv

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'backend'))

# Load environment variables from backend/.env
load_dotenv(os.path.join(project_root, 'backend', '.env'))

from backend.db.database import SessionLocal
from backend.db.models import User

INPUT_SKILLS_CSV = "harvested_skills_deduped.csv"

def import_skills():
    if not os.path.exists(INPUT_SKILLS_CSV):
        print(f"File not found: {INPUT_SKILLS_CSV}")
        return

    print(f"Reading {INPUT_SKILLS_CSV}...")
    df = pd.read_csv(INPUT_SKILLS_CSV)
    new_skills = df['Skill'].tolist()
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == 1).first()
        if not user:
            print("User 1 not found")
            return
        
        # Initialize candidate_profile if None
        if not user.candidate_profile:
            user.candidate_profile = {}
            
        # Get existing skills
        # Assuming structure: candidate_profile['linkedin_meta']['top_skills'] or similar
        # Based on models.py comments: "linkedin_meta (headline, about, top_skills, open_to_work_titles)"
        
        profile = user.candidate_profile
        if 'linkedin_meta' not in profile:
            profile['linkedin_meta'] = {}
            
        existing_skills = profile['linkedin_meta'].get('top_skills', [])
        
        # Merge and dedupe
        # Normalize for comparison but keep original casing from new list if possible
        existing_lower = {s.lower() for s in existing_skills}
        
        added_count = 0
        for skill in new_skills:
            if skill.lower() not in existing_lower:
                existing_skills.append(skill)
                existing_lower.add(skill.lower())
                added_count += 1
                
        profile['linkedin_meta']['top_skills'] = existing_skills
        
        # Update user
        # Need to re-assign to trigger change detection for JSON field in some ORMs, 
        # though SQLAlchemy usually handles it if mutable. 
        # Safest is to re-assign.
        user.candidate_profile = dict(profile)
        
        db.commit()
        print(f"Successfully added {added_count} new skills to User 1 profile.")
        print(f"Total skills: {len(existing_skills)}")
            
    except Exception as e:
        print(f"Error importing skills: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import_skills()
