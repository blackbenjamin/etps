import os
import re
import sys
import glob
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional
from docx import Document
import json
import asyncio
from dotenv import load_dotenv

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'backend'))

# Load environment variables from backend/.env
load_dotenv(os.path.join(project_root, 'backend', '.env'))

from backend.services.llm import create_llm

# Configuration
TARGET_DIR = "/Users/benjaminblack/Library/CloudStorage/GoogleDrive-black.benjamin@gmail.com/My Drive/__Career - Recruiting-"
MAX_RESUMES_PER_YEAR = 3
OUTPUT_BULLETS_CSV = "harvested_bullets.csv"
OUTPUT_SKILLS_CSV = "harvested_skills.csv"

def parse_date_from_filename(filename: str) -> Optional[datetime]:
    """Extract YYYYMMDD date from filename."""
    match = re.search(r"(\d{8})", filename)
    if match:
        try:
            return datetime.strptime(match.group(1), "%Y%m%d")
        except ValueError:
            return None
    return None

def get_target_files(directory: str) -> List[Dict]:
    """
    Scan directory for DOCX files, parse dates, and select top N per year.
    Returns list of dicts: {'path': str, 'date': datetime, 'year': int}
    """
    files_data = []
    print(f"Scanning directory: {directory}")
    
    # Walk directory recursively
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(".docx") and not file.startswith("~$"):
                full_path = os.path.join(root, file)
                date_obj = parse_date_from_filename(file)
                
                if date_obj:
                    files_data.append({
                        "path": full_path,
                        "filename": file,
                        "date": date_obj,
                        "year": date_obj.year
                    })
    
    # Group by year and select top N
    df = pd.DataFrame(files_data)
    if df.empty:
        print("No valid DOCX files with YYYYMMDD dates found.")
        return []
        
    selected_files = []
    for year, group in df.groupby("year"):
        # Sort by date descending (newest first)
        top_n = group.sort_values("date", ascending=False).head(MAX_RESUMES_PER_YEAR)
        selected_files.extend(top_n.to_dict("records"))
        
    print(f"Found {len(files_data)} total files. Selected {len(selected_files)} for processing.")
    return selected_files

def extract_text_from_docx(docx_path: str) -> str:
    """Read full text from DOCX file."""
    try:
        doc = Document(docx_path)
        full_text = []
        for para in doc.paragraphs:
            if para.text.strip():
                full_text.append(para.text.strip())
        return "\n".join(full_text)
    except Exception as e:
        print(f"Error reading {docx_path}: {e}")
        return ""

async def extract_structured_data(text: str, llm) -> Dict:
    """Use LLM to extract structured experience and skills."""
    prompt = f"""
    You are an expert resume parser. Extract structured data from the following resume text.
    
    Output strictly valid JSON with this schema:
    {{
        "experiences": [
            {{
                "employer": "Company Name",
                "job_title": "Job Title",
                "start_date": "YYYY-MM or YYYY",
                "end_date": "YYYY-MM or Present",
                "bullets": ["bullet 1", "bullet 2"]
            }}
        ],
        "skills": ["Skill 1", "Skill 2", "Skill 3"]
    }}
    
    Resume Text:
    {text[:15000]}  # Truncate to avoid token limits if very large
    """
    
    try:
        response = await llm.generate_text(prompt, max_tokens=4096)
        # Extract JSON using regex to handle extra text
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            cleaned_response = match.group(0)
            return json.loads(cleaned_response)
        else:
            print("No JSON found in response")
            return {"experiences": [], "skills": []}
    except Exception as e:
        print(f"LLM Extraction failed: {e}")
        print(f"Raw Response: {response[:100]}...") # Print first 100 chars
        return {"experiences": [], "skills": []}

async def main():
    print("Starting Resume Harvester...")
    
    # 1. Get Files
    target_files = get_target_files(TARGET_DIR)
    if not target_files:
        return

    # 2. Initialize LLM
    llm = create_llm()
    print(f"LLM Initialized: {type(llm).__name__}")
    
    all_bullets = []
    all_skills = []
    
    # 3. Process Files
    for i, file_info in enumerate(target_files):
        print(f"Processing [{i+1}/{len(target_files)}]: {file_info['filename']} ({file_info['date'].strftime('%Y-%m-%d')})")
        
        text = extract_text_from_docx(file_info['path'])
        if not text:
            continue
            
        data = await extract_structured_data(text, llm)
        
        # Collect Bullets
        for exp in data.get("experiences", []):
            for bullet in exp.get("bullets", []):
                all_bullets.append({
                    "ResumeDate": file_info['date'].strftime("%Y-%m-%d"),
                    "SourceFile": file_info['filename'],
                    "Employer": exp.get("employer", "Unknown"),
                    "JobTitle": exp.get("job_title", "Unknown"),
                    "BulletText": bullet
                })
                
        # Collect Skills
        for skill in data.get("skills", []):
            all_skills.append({
                "ResumeDate": file_info['date'].strftime("%Y-%m-%d"),
                "SourceFile": file_info['filename'],
                "Skill": skill
            })
            
    # 4. Save CSVs
    if all_bullets:
        df_bullets = pd.DataFrame(all_bullets)
        df_bullets.to_csv(OUTPUT_BULLETS_CSV, index=False)
        print(f"Saved {len(df_bullets)} bullets to {OUTPUT_BULLETS_CSV}")
    
    if all_skills:
        df_skills = pd.DataFrame(all_skills)
        df_skills.to_csv(OUTPUT_SKILLS_CSV, index=False)
        print(f"Saved {len(df_skills)} skills to {OUTPUT_SKILLS_CSV}")

if __name__ == "__main__":
    asyncio.run(main())
