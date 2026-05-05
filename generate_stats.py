#!/usr/bin/env python3
"""
GitHub Profile README Generator
Generates dynamic stats, charts, and content for MrTrotid's profile
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


def generate_skill_bar_html(lang_stats):
    """Generate HTML skill bars for README"""
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
    
    html = '<div align="center">\n'
    for lang, percentage in lang_stats:
        color = colors.get(lang, "#3B82F6")
        bar_width = min(int(percentage * 2), 100)
        html += f'''
<div style="margin: 10px 0;">
  <div style="display: flex; align-items: center; gap: 10px;">
    <span style="min-width: 100px; text-align: right;">{lang}</span>
    <div style="flex-grow: 1; background: #e0e0e0; border-radius: 10px; height: 20px; overflow: hidden;">
      <div style="width: {bar_width}%; background: {color}; height: 100%; border-radius: 10px; transition: width 0.5s;"></div>
    </div>
    <span style="min-width: 50px;">{percentage:.1f}%</span>
  </div>
</div>'''
    html += '\n</div>'
    return html


def generate_readme_content(user_data, repos_data, lang_stats):
    """Generate the complete README content"""
    
    # Calculate stats
    public_repos = user_data.get('public_repos', 0)
    followers = user_data.get('followers', 0)
    
    # Calculate total stars
    total_stars = sum(repo.get('stargazers_count', 0) for repo in repos_data)
    
    # Generate skill bars
    skill_bars = generate_skill_bar_html(lang_stats)
    
    readme = f'''# <div align="center">Baman Prasad Guragain</div>

<div align="center">

### `Cybersecurity Enthusiast & Creative Developer`

<img src="https://readme-typing-svg.herokuapp.com?font=Fira+Code&size=22&duration=3000&pause=1000&color=3B82F6&center=true&vCenter=true&width=600&lines=Learning+Cybersecurity+%F0%9F%94%90;Building+cool+things+%F0%9F%9A%80;Python+%7C+SQL+%7C+ESP32+%F0%9F%94%A5;Student+%40+Nepal+%F0%9F%87%B3%F0%9F%87%B5" alt="Typing SVG" />

</div>

---

## 🎯 About Me

```python
class MrTrotid:
    def __init__(self):
        self.name = "Baman Prasad Guragain"
        self.role = "Student & Cybersecurity Learner"
        self.location = "Nepal 🇳🇵"
        self.focus = ["Cybersecurity", "Python", "SQL", "IoT (ESP32)"]
        self.current_learning = "Ethical Hacking & Network Security"
        
    def get_motto(self):
        return "It's all vibe coding until it works! 🎧"
    
    def get_status(self):
        return "🔭 Exploring the intersection of code and security"
```

<p align="center">
  <img src="https://komarev.com/ghpvc/?username={USERNAME}&style=for-the-badge&color=3B82F6" alt="Profile Views" />
</p>

---

## 🛠️ Tech Stack & Skills

<div align="center">

### 💻 Languages
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![SQL](https://img.shields.io/badge/SQL-336791?style=for-the-badge&logo=mysql&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)

### 🔌 IoT & Hardware
![ESP32](https://img.shields.io/badge/ESP32-000000?style=for-the-badge&logo=espressif&logoColor=white)
![Arduino](https://img.shields.io/badge/Arduino-00979D?style=for-the-badge&logo=arduino&logoColor=white)
![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-A22846?style=for-the-badge&logo=raspberry-pi&logoColor=white)

### 🛡️ Security & Tools
![Cisco](https://img.shields.io/badge/Cisco-1BA0D7?style=for-the-badge&logo=cisco&logoColor=white)
![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)
![Git](https://img.shields.io/badge/Git-F05032?style=for-the-badge&logo=git&logoColor=white)
![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)

</div>

### 📊 Language Distribution

{skill_bars}

---

## 📊 GitHub Analytics

<div align="center">

<img src="https://github-readme-stats.vercel.app/api?username={USERNAME}&show_icons=true&theme=default&hide_border=true&count_private=true&include_all_commits=true&icon_color=3B82F6&title_color=3B82F6&text_color=333&bg_color=ffffff00" alt="GitHub Stats" width="400"/>

<img src="https://github-readme-streak-stats.herokuapp.com/?user={USERNAME}&theme=default&hide_border=true&background=ffffff00&stroke=3B82F6&ring=3B82F6&fire=3B82F6&currStreakLabel=3B82F6" alt="GitHub Streak" width="400"/>

<img src="https://github-readme-stats.vercel.app/api/top-langs/?username={USERNAME}&layout=compact&theme=default&hide_border=true&count_private=true&bg_color=ffffff00&title_color=3B82F6&text_color=333" alt="Top Languages" width="400"/>

</div>

---

## 🚀 Featured Projects

<div align="center">

### 🔍 Sherlock Scramble Solver
*A Python tool to solve 15x15 grid word games*
<br>
[![Repo](https://img.shields.io/badge/View%20Repository-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/{USERNAME}/Sherlock-Scramble-Solver)
![Stars](https://img.shields.io/github/stars/{USERNAME}/Sherlock-Scramble-Solver?style=for-the-badge&color=3B82F6)

### 🎮 Weave Game
*Word search game built with Next.js, Auth.js, TailwindCSS & Firestore*
<br>
[![Repo](https://img.shields.io/badge/View%20Repository-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/{USERNAME}/Weave-Game)
![Stars](https://img.shields.io/github/stars/{USERNAME}/Weave-Game?style=for-the-badge&color=3B82F6)

### 🌐 Portfolio Website
*Clean portfolio to showcase my projects and skills*
<br>
[![Repo](https://img.shields.io/badge/View%20Repository-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/{USERNAME}/portfolio-website)
![Stars](https://img.shields.io/github/stars/{USERNAME}/portfolio-website?style=for-the-badge&color=3B82F6)

</div>

---

## 🏆 Achievements & Certifications

<div align="center">

![3rd Place Cambridge Code League](https://img.shields.io/badge/3rd%20Place-Cambridge%20Code%20League-blue?style=for-the-badge)
![Best UI/UX](https://img.shields.io/badge/Best%20UI%2FUX-Cambridge%20Code%20League-green?style=for-the-badge)
![1st Place STEAM Exhibition](https://img.shields.io/badge/1st%20Place-STEAM%20Exhibition-orange?style=for-the-badge)

### 🎓 Certifications
![Cisco Networking Basics](https://img.shields.io/badge/Cisco-Networking%20Basics-1BA0D7?style=for-the-badge&logo=cisco&logoColor=white)
![Cisco Intro to Cybersecurity](https://img.shields.io/badge/Cisco-Intro%20to%20Cybersecurity-1BA0D7?style=for-the-badge&logo=cisco&logoColor=white)

</div>

---

## 🌐 Let's Connect

<div align="center">

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com/in/mrtrotid)
[![Portfolio](https://img.shields.io/badge/Portfolio-bamanguragain.com.np-FF7139?style=for-the-badge&logo=google-chrome&logoColor=white)](https://bamanguragain.com.np)
[![Projects](https://img.shields.io/badge/Projects-Site-10B981?style=for-the-badge&logo=react&logoColor=white)](https://projects.bamanguragain.com.np)
[![Certifications](https://img.shields.io/badge/Certifications-Site-8B5CF6?style=for-the-badge&logo=academia&logoColor=white)](https://certifications.bamanguragain.com.np)

<br>

[![X (Twitter)](https://img.shields.io/badge/X-000000?style=for-the-badge&logo=x&logoColor=white)](https://x.com/MrTrotid)
[![YouTube](https://img.shields.io/badge/YouTube-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://youtube.com/@mrtrotid)
[![Instagram](https://img.shields.io/badge/Instagram-E4405F?style=for-the-badge&logo=instagram&logoColor=white)](https://instagram.com/mrtrotid)
[![Email](https://img.shields.io/badge/Email-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:contact@bamanguragain.com.np)

</div>

---

## 🐍 GitHub Activity Snake

<div align="center">

![GitHub Snake Animation](https://raw.githubusercontent.com/{USERNAME}/{USERNAME}/output/github-contribution-grid-snake.svg)

</div>

---

## 🎮 Interactive Stats Card

<div align="center">

<img src="https://github-readme-activity-graph.vercel.app/graph?username={USERNAME}&theme=minimal&hide_border=true&area=true&color=3B82F6&line=3B82F6&point=3B82F6" alt="Activity Graph" />

</div>

---

## 💡 Random Dev Quote

<div align="center">

[![](https://quotes-github-readme.vercel.app/api?type=horizontal&theme=light)](https://github.com/piyushsethi03)

</div>

---

<div align="center">

### 📈 Live Visitor Counter

<img src="https://visitcount.itsvg.in/api?id={USERNAME}&icon=3&color=3B82F6" alt="Visitor Count" />

<br><br>

**💖 Thanks for visiting! Let's connect and build something amazing together 🚀**

<img src="https://capsule-render.vercel.app/api?type=waving&color=3B82F6&height=120&section=footer&fontColor=ffffff" width="100%"/>

</div>

<!-- Generated with ❤️ by generate_stats.py -->
<!-- Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} '''
    return readme


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
        
        print("📝 Generating README content...")
        readme_content = generate_readme_content(user_data, repos_data, lang_stats)
        
        # Save README
        with open("README.md", "w", encoding="utf-8") as f:
            f.write(readme_content)
        print("✅ README.md generated successfully!")
        
        # Save stats JSON
        save_stats_json(user_data, repos_data)
        print("✅ stats.json saved!")
        
        # Save language stats
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(f"{OUTPUT_DIR}/lang_stats.json", "w") as f:
            json.dump(lang_stats, f)
        print("✅ lang_stats.json saved!")
        
        print("\n🎉 All done! Your README.md is ready.")
        print("💡 Tip: Run this script periodically to update your stats!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure you have an internet connection and the requests library installed.")
        print("Install it with: pip install requests")


if __name__ == "__main__":
    main()
