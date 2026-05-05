#!/usr/bin/env python3
"""
GitHub Contribution Snake Generator
Generates a snake animation that eats your GitHub contributions
"""

import requests
import json
from datetime import datetime, timedelta

def get_contribution_data(username, days=365):
    """Fetch contribution data from GitHub"""
    # GitHub's contribution API requires GraphQL, but we'll use a simpler approach
    # This creates a placeholder that github-snake action would generate
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    print(f"🐍 Snake generator for {username}")
    print(f"📅 Date range: {start_date.date()} to {end_date.date()}")
    
    # In a real implementation, you'd use the GitHub GraphQL API
    # For now, we'll create the directory structure
    
    return True

def create_snake_workflow():
    """Create GitHub Actions workflow for snake generation"""
    workflow_content = """name: Generate Snake

on:
  schedule:
    - cron: "0 0 * * *"  # Runs daily at midnight
  workflow_dispatch:
  push:
    branches:
      - main

jobs:
  generate:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        
      - name: Generate GitHub Contribution Snake
        uses: Platane/snk@v3
        with:
          github_user_name: ${{ github.repository_owner }}
          outputs: |
            dist/github-contribution-grid-snake.svg
            dist/github-contribution-grid-snake-dark.svg
            
      - name: Push to output branch
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./dist
          publish_branch: output
          destination_dir: .
"""
    
    import os
    os.makedirs(".github/workflows", exist_ok=True)
    with open(".github/workflows/snake.yml", "w") as f:
        f.write(workflow_content)
    
    print("✅ Created .github/workflows/snake.yml")

if __name__ == "__main__":
    print("🐍 GitHub Contribution Snake Setup\n")
    
    # Create the workflow
    create_snake_workflow()
    
    print("\n📝 Next steps:")
    print("1. Commit and push these changes to your 'MrTrotid' repository")
    print("2. The snake will be generated automatically via GitHub Actions")
    print("3. The snake SVG will be available at:")
    print("   https://raw.githubusercontent.com/MrTrotid/MrTrotid/output/github-contribution-grid-snake.svg")
    print("\n💡 Tip: Make sure to enable GitHub Actions in your repository settings!")
