#!/usr/bin/env python3
"""
GitHub Profile README Generator for MrTrotid
Generates dynamic stats and content for GitHub profile README
"""

import requests
import json
from datetime import datetime
import os

# Configuration
USERNAME = "MrTrotid"
OUTPUT_DIR = "generated"

def fetch_github_data(username):
    """Fetch user and repo data from GitHub API"""
    headers = {"Accept": "application/vnd.github.v3+json"}
    
    # Fetch user info
    user_url = f"https://api.github.com/users/{username}"
    user_response = requests.get(user_url, headers=headers)
    user_data = user_response.json()
    
    # Fetch repos
    repos_url = f"https://api.github.com/users/{username}/repos?per_page=100"
    repos_response = requests.get(repos_url, headers=headers)
    repos_data = repos_response.json()
    
    return user_data, repos_data

def calculate_language_stats(repos_data):
    """Calculate language usage statistics"""
    languages = {}
    total_bytes = 0
    
    for repo in repos_data:
        if repo.get('language'):
            lang = repo['language']
            # Fetch repo languages
            if repo.get('languages_url'):
                try:
                    lang_response = requests.get(repo['languages_url'])
                    lang_data = lang_response.json()
                    for language, bytes_count in lang_data.items():
                        languages[language] = languages.get(language, 0) + bytes_count
                        total_bytes += bytes_count
                except:
                    pass
    
    # Calculate percentages
    lang_percentages = {}
    if total_bytes > 0:
        for lang, bytes_count in languages.items():
            lang_percentages[lang] = (bytes_count / total_bytes) * 100
    
    return sorted(lang_percentages.items(), key=lambda x: x[1], reverse=True)[:8]

def generate_skill_bars(lang_stats):
    """Generate markdown skill bars"""
    colors = {
        "Python": "#3776AB",
        "JavaScript": "#F7DF1E",
        "TypeScript": "#3178C6",
        "HTML": "#E34F26",
        "CSS": "#1572B6",
        "SQL": "#336791",
        "C++": "#00599C",
        "Java": "#ED8B00"
    }
    
    bars = []
    for lang, percentage in lang_stats:
        color = colors.get(lang, "#3B82F6")
        bar = f"![{lang}](https://img.shields.io/badge/{lang}-{percentage:.1f}%25-{color[1:]})"
        bars.append(bar)
    
    return "\n".join(bars)

def save_stats_json(user_data, repos_data):
    """Save stats to JSON for dynamic badges"""
    stats = {
        "stars": sum(repo.get('stargazers_count', 0) for repo in repos_data),
        "repos": user_data.get('public_repos', 0),
        "followers": user_data.get('followers', 0),
        "total": sum(repo.get('stargazers_count', 0) for repo in repos_data) + user_data.get('public_repos', 0) + user_data.get('followers', 0)
    }
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(f"{OUTPUT_DIR}/stats.json", "w") as f:
        json.dump(stats, f)

def main():
    """Main function"""
    print(f"🔍 Fetching GitHub data for {USERNAME}...")
    
    try:
        user_data, repos_data = fetch_github_data(USERNAME)
        
        print("📊 Calculating language statistics...")
        lang_stats = calculate_language_stats(repos_data)
        
        print("💾 Saving stats JSON...")
        save_stats_json(user_data, repos_data)
        
        # Generate skill bars markdown
        skill_bars = generate_skill_bars(lang_stats)
        
        print("\n✅ Stats generated successfully!")
        print(f"📁 Check the '{OUTPUT_DIR}' folder for stats.json")
        print("\n📊 Top languages:")
        for lang, pct in lang_stats:
            print(f"  - {lang}: {pct:.1f}%")
        
        print("\n💡 Now run: python generate_readme_content.py")
        print("   (This will create the actual README.md with the stats)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure you have an internet connection and the requests library installed.")
        print("Install it with: pip install requests")

if __name__ == "__main__":
    main()
