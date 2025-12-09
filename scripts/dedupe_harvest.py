import pandas as pd
import os

# Configuration
INPUT_BULLETS_CSV = "harvested_bullets.csv"
INPUT_SKILLS_CSV = "harvested_skills.csv"
OUTPUT_BULLETS_DEDUPED = "harvested_bullets_deduped.csv"
OUTPUT_SKILLS_DEDUPED = "harvested_skills_deduped.csv"

def dedupe_bullets():
    if not os.path.exists(INPUT_BULLETS_CSV):
        print(f"File not found: {INPUT_BULLETS_CSV}")
        return

    print(f"Reading {INPUT_BULLETS_CSV}...")
    df = pd.read_csv(INPUT_BULLETS_CSV)
    
    # Sort by Date descending so the first occurrence is the latest
    df['ResumeDate'] = pd.to_datetime(df['ResumeDate'])
    df = df.sort_values('ResumeDate', ascending=False)
    
    # Deduplicate based on BulletText (keeping first/latest)
    # We also consider Employer/JobTitle to be part of the identity? 
    # User said "most recent entry for each bullet". 
    # If the same bullet text appears for different employers, it's likely a duplicate or generic bullet.
    # Let's stick to BulletText as the unique key to be aggressive about deduping.
    original_count = len(df)
    df_deduped = df.drop_duplicates(subset=['BulletText'], keep='first')
    
    print(f"Bullets: {original_count} -> {len(df_deduped)} (Removed {original_count - len(df_deduped)} duplicates)")
    
    df_deduped.to_csv(OUTPUT_BULLETS_DEDUPED, index=False)
    print(f"Saved to {OUTPUT_BULLETS_DEDUPED}")

def dedupe_skills():
    if not os.path.exists(INPUT_SKILLS_CSV):
        print(f"File not found: {INPUT_SKILLS_CSV}")
        return

    print(f"Reading {INPUT_SKILLS_CSV}...")
    df = pd.read_csv(INPUT_SKILLS_CSV)
    
    # Sort by Date descending
    df['ResumeDate'] = pd.to_datetime(df['ResumeDate'])
    df = df.sort_values('ResumeDate', ascending=False)
    
    # Deduplicate based on Skill (keeping first/latest)
    # Normalize skill text (lowercase) for better deduping?
    # User didn't explicitly ask for normalization, but it's usually good.
    # For now, let's do exact match to be safe, or maybe case-insensitive?
    # Let's do exact match first to preserve original casing preference.
    original_count = len(df)
    df_deduped = df.drop_duplicates(subset=['Skill'], keep='first')
    
    print(f"Skills: {original_count} -> {len(df_deduped)} (Removed {original_count - len(df_deduped)} duplicates)")
    
    df_deduped.to_csv(OUTPUT_SKILLS_DEDUPED, index=False)
    print(f"Saved to {OUTPUT_SKILLS_DEDUPED}")

if __name__ == "__main__":
    dedupe_bullets()
    print("-" * 20)
    dedupe_skills()
