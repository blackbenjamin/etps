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

MANUAL_SKILLS = [
    "AI", "Agile/Scrum", "Algorithms", "AI Architecture", "AI Project Mgmt", "AI Strategy", 
    "AI Governance", "AI Ethics", "Analytics", "Analytics Strategy", "Architecture", "AWS", 
    "Azure", "Big Data", "Bloomberg", "Business Analysis", "Business Intelligence", 
    "Business Process", "Business Strategy", "Change Management", "Cloud Computing", "Coding", 
    "Communication", "Competition", "Compliance", "Consulting", "Content Strategy", 
    "Data Analysis", "Data Architecture", "Data Governance", "Data Lake", "Data Mining", 
    "Data Modeling", "Data Privacy", "Data Science", "Data Strategy", "Data Visualization", 
    "Data Warehouse", "Deep Learning", "Design Thinking", "DevOps", "Digital Strategy", 
    "Digital Transformation", "Economics", "Enterprise Architecture", "Entrepreneurship", 
    "Equity Research", "Excel", "Finance", "Financial Analysis", "Financial Modeling", 
    "Fintech", "GCP", "Git", "GitHub", "Go-to-Market", "Hadoop", "Hive", "HTML/CSS", 
    "Innovation", "Investment Management", "Java", "JavaScript", "JIRA", "Leadership", 
    "Machine Learning", "Management Consulting", "Marketing", "Matlab", "Microsoft Office", 
    "ML", "NLP", "NoSQL", "Operations", "Oracle", "Product Management", "Project Management", 
    "Python", "R", "Research", "Risk Management", "Salesforce", "Scrum", "Software Development", 
    "SQL", "Statistics", "Strategic Planning", "Strategy", "Tableau", "Team Leadership", 
    "Technology", "Technology Strategy", "TensorFlow", "Trading", "VBA", "Visio", 
    "Web Development", "Word", "XML"
]

def import_manual_skills():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == 1).first()
        if not user:
            print("User 1 not found")
            return
        
        # Initialize candidate_profile if None
        if not user.candidate_profile:
            user.candidate_profile = {}
            
        profile = user.candidate_profile
        if 'linkedin_meta' not in profile:
            profile['linkedin_meta'] = {}
            
        existing_skills = profile['linkedin_meta'].get('top_skills', [])
        
        # Merge and dedupe
        existing_lower = {s.lower() for s in existing_skills}
        
        added_count = 0
        for skill in MANUAL_SKILLS:
            if skill.lower() not in existing_lower:
                existing_skills.append(skill)
                existing_lower.add(skill.lower())
                added_count += 1
                
        profile['linkedin_meta']['top_skills'] = existing_skills
        
        # Update user
        user.candidate_profile = dict(profile)
        
        db.commit()
        print(f"Successfully added {added_count} new skills from manual list to User 1 profile.")
        print(f"Total skills: {len(existing_skills)}")
            
    except Exception as e:
        print(f"Error importing skills: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import_manual_skills()
