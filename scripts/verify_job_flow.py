import json
import sys
import urllib.request
import urllib.error

API_BASE = "http://localhost:8000/api/v1"

def make_request(endpoint, data=None):
    url = f"{API_BASE}{endpoint}"
    headers = {'Content-Type': 'application/json'}
    
    try:
        if data:
            json_data = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(url, data=json_data, headers=headers)
        else:
            req = urllib.request.Request(url, headers=headers)
            
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error {e.code}: {e.reason}")
        print(e.read().decode('utf-8'))
        raise
    except Exception as e:
        print(f"❌ Request Failed: {e}")
        raise

def run_verification(jd_text):
    print(f"Starting verification with JD length: {len(jd_text)} chars")
    
    # 1. Parse Job Description
    print("\n1. Parsing Job Description...")
    try:
        job_profile = make_request("/job/parse", {"jd_text": jd_text, "user_id": 1})
        print("✅ Job Parsed Successfully")
        print(f"   Title: {job_profile.get('job_title')}")
        print(f"   Company: {job_profile.get('company_name')}")
        print(f"   Skills Found: {len(job_profile.get('extracted_skills', []))}")
        print(f"   ID: {job_profile.get('job_profile_id')}")
    except Exception:
        return

    job_id = job_profile.get('job_profile_id')

    # 2. Analyze Skill Gap
    print("\n2. Analyzing Skill Gap...")
    try:
        gap_analysis = make_request("/job/skill-gap", {"job_profile_id": job_id, "user_id": 1})
        print("✅ Skill Gap Analysis Complete")
        print(f"   Match Score: {gap_analysis.get('match_score')}%")
        print(f"   Missing Skills: {len(gap_analysis.get('missing_skills', []))}")
    except Exception:
        pass # Continue anyway
    
    # 3. Generate Resume
    print("\n3. Generating Resume...")
    try:
        resume = make_request("/resume/generate", {"job_profile_id": job_id, "user_id": 1})
        print("✅ Resume Generated Successfully")
        print(f"   ATS Score: {resume.get('ats_score_estimate')}")
        print(f"   Summary: {resume.get('tailored_summary')[:100]}...")
    except Exception:
        pass

if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            jd_text = f.read()
    else:
        print("Please provide a file path argument")
        sys.exit(1)
        
    run_verification(jd_text)
