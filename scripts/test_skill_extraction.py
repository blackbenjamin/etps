import sys
import os
import re

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.job_parser import extract_skills_keywords

def test_extraction():
    with open('sample_jd.txt', 'r') as f:
        jd_text = f.read()
    
    print(f"JD Length: {len(jd_text)}")
    
    skills = extract_skills_keywords(jd_text)
    print("\nExtracted Skills:")
    for skill in skills:
        print(f"- {skill}")

    # Check for expected skills
    expected = [
        'AI', 'Artificial Intelligence', 'Data Science', 
        'Sales', 'Business Development', 'Marketing', 
        'Solution Architecture', 'Cloud Architecture'
    ]
    
    print("\nMissing Expected Skills:")
    for skill in expected:
        if skill not in skills:
            print(f"- {skill}")

if __name__ == "__main__":
    test_extraction()
