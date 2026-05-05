# 🚀 Setup Guide - MrTrotid's Awesome README

## 📁 Files Created

### Python Scripts
1. **generate_stats.py** - Fetches GitHub data and generates stats
2. **generate_readme.py** - Generates README content with dynamic data
3. **generate_snake.py** - Sets up GitHub contribution snake

### Configuration Files
1. **requirements.txt** - Python dependencies
2. **.github/workflows/update-readme.yml** - Auto-updates README every 6 hours
3. **.github/workflows/snake.yml** - Generates contribution snake daily

### Generated Files
1. **README.md** - Your awesome profile README (already created)
2. **generated/stats.json** - Dynamic stats for badges
3. **generated/lang_stats.json** - Language statistics

---

## 🛠️ How to Use

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Generate Your README
```bash
# Fetch stats and generate JSON files
python3 generate_stats.py

# The README.md is already created with all features!
```

### Step 3: Set Up GitHub Actions (Automation)
1. Create a repository named `MrTrotid` (if not exists)
2. Commit and push all files to the repository
3. Go to repository Settings → Actions → Enable Actions
4. The workflows will:
   - Update README every 6 hours
   - Generate contribution snake daily

### Step 4: Enable GitHub Pages (for Snake)
1. Go to Settings → Pages
2. Set source to "output" branch
3. The snake will be available at:
   `https://raw.githubusercontent.com/MrTrotid/MrTrotid/output/github-contribution-grid-snake.svg`

---

## 🎨 Features Included

✅ **Typing Animation** - Dynamic text that types itself  
✅ **GitHub Stats Cards** - Auto-updating stats, streak, top languages  
✅ **Tech Stack Badges** - Python, SQL, ESP32, Arduino, etc.  
✅ **Featured Projects** - With star counts and descriptions  
✅ **Achievement Badges** - Cambridge Code League, STEAM Exhibition  
✅ **Social Links** - LinkedIn, Portfolio, YouTube, Instagram  
✅ **GitHub Activity Snake** - Animated contribution graph  
✅ **Activity Graph** - Interactive contribution graph  
✅ **Random Dev Quotes** - Fresh quote on every visit  
✅ **Visitor Counter** - Live profile view counter  
✅ **Surprise Zone** - Hidden easter egg with GIF  

---

## 🔄 Automation

Once pushed to GitHub, the workflows will:
- **update-readme.yml** - Runs every 6 hours to update stats
- **snake.yml** - Generates contribution snake daily

You can also trigger manually:
- Go to Actions tab → Select workflow → "Run workflow"

---

## 💡 Tips

1. **Test locally**: Run `python3 generate_stats.py` to see your current stats
2. **Customize**: Edit the Python scripts to change colors, text, or features
3. **Force update**: Delete `generated/stats.json` and re-run the script
4. **Check Actions**: Visit the Actions tab to see workflow runs

---

## 🎉 You're All Set!

Your GitHub profile will now have:
- Modern, minimalist design
- Live-updating stats
- Cool animations and interactions
- Professional yet creative look

**Go push it and see the magic!** 🚀
