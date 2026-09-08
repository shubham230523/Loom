import os
import subprocess
import shutil
import re

repo_url = "https://github.com/shubham230523/AIMastery.git"
temp_dir = "temp_ai_mastery"

if os.path.exists(temp_dir):
    shutil.rmtree(temp_dir)

print(f"Cloning {repo_url}...")
subprocess.run(["git", "clone", "--depth", "1", repo_url, temp_dir], check=True)

todo_pattern = re.compile(r"TODO[:\s]+(.+)", re.IGNORECASE)

print("\n--- Scanning for TODOs ---")
found = 0
for root, dirs, files in os.walk(temp_dir):
    for file in files:
        if file.endswith(".md"):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    for i, line in enumerate(f, 1):
                        match = todo_pattern.search(line)
                        if match:
                            print(f"[{file}:{i}] {match.group(0).strip()}")
                            found += 1
            except Exception as e:
                print(f"Error reading {path}: {e}")

print(f"\nTotal TODOs found in Markdown: {found}")

shutil.rmtree(temp_dir)
