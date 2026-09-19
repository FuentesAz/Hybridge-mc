#!/usr/bin/env python3
import os
import json
import urllib.request

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSIONS_FILE_PATH = os.path.join(REPO_ROOT, "version.json")
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) BedrockServerUpdater/1.0"

def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))

def load_versions():
    if os.path.exists(VERSIONS_FILE_PATH):
        try:
            with open(VERSIONS_FILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_versions(versions):
    with open(VERSIONS_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(versions, f, indent=2)

def check_bedrock_image(stored_version):
    print("Checking for Bedrock Server updates...")
    try:
        url = "https://api.github.com/repos/itzg/docker-minecraft-bedrock-server/releases/latest"
        data = fetch_json(url)
        tag_name = data.get("tag_name", "")
        if tag_name and tag_name != stored_version:
            print(f"  -> Bedrock image update found: {stored_version} => {tag_name}")
            return True, tag_name
    except Exception as e:
        print(f"  -> Failed to check Bedrock release: {e}")
    print(f"  -> Bedrock image is up to date ({stored_version}).")
    return False, stored_version

def main():
    versions = load_versions()
    changes = []

    bedrock_updated, new_version = check_bedrock_image(versions.get("bedrock_image_version"))
    if bedrock_updated:
        changes.append(f"Bedrock Server {new_version}")
        versions["bedrock_image_version"] = new_version

    if changes:
        save_versions(versions)
        commit_msg = "auto: update " + ", ".join(changes)
        print(f"\nUpdates completed! Commit message: {commit_msg}")
        
        github_output = os.environ.get("GITHUB_OUTPUT")
        if github_output:
            with open(github_output, "a", encoding="utf-8") as f:
                f.write("has_updates=true\n")
                f.write(f"commit_message={commit_msg}\n")
    else:
        print("\nNo updates found.")
        github_output = os.environ.get("GITHUB_OUTPUT")
        if github_output:
            with open(github_output, "a", encoding="utf-8") as f:
                f.write("has_updates=false\n")

if __name__ == "__main__":
    main()
