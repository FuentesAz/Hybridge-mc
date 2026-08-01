#!/usr/bin/env python3
import os
import re
import json
import urllib.request

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCKERFILE_PATH = os.path.join(REPO_ROOT, "Dockerfile")
VERSIONS_FILE_PATH = os.path.join(REPO_ROOT, "plugins", ".versions.json")
PLUGINS_DIR = os.path.join(REPO_ROOT, "plugins")

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MinecraftServerUpdater/1.0"

def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))

def download_file(url, target_path):
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req) as response, open(target_path, "wb") as out_file:
        out_file.write(response.read())

def load_versions():
    if os.path.exists(VERSIONS_FILE_PATH):
        try:
            with open(VERSIONS_FILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_versions(versions):
    os.makedirs(os.path.dirname(VERSIONS_FILE_PATH), exist_ok=True)
    with open(VERSIONS_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(versions, f, indent=2)

def check_spigot():
    print("Checking for Spigot updates...")
    url = "https://launchermeta.mojang.com/mc/game/version_manifest_v2.json"
    data = fetch_json(url)
    
    # Filter for standard Minecraft 1.x release versions
    releases = [
        v["id"] for v in data.get("versions", [])
        if v.get("type") == "release" and re.match(r"^1\.\d+(\.\d+)?$", v.get("id", ""))
    ]
    latest_version = releases[0] if releases else "1.21.4"
    
    current_version = None
    if os.path.exists(DOCKERFILE_PATH):
        with open(DOCKERFILE_PATH, "r", encoding="utf-8") as f:
            content = f.read()
            match = re.search(r"ARG\s+SPIGOT_VERSION=([^\s]+)", content)
            if match:
                current_version = match.group(1)

    if latest_version and latest_version != current_version:
        print(f"  -> Spigot update found: {current_version} => {latest_version}")
        if os.path.exists(DOCKERFILE_PATH):
            with open(DOCKERFILE_PATH, "r", encoding="utf-8") as f:
                content = f.read()
            new_content = re.sub(r"ARG\s+SPIGOT_VERSION=[^\s]+", f"ARG SPIGOT_VERSION={latest_version}", content)
            with open(DOCKERFILE_PATH, "w", encoding="utf-8") as f:
                f.write(new_content)
        return True, current_version, latest_version
    else:
        print(f"  -> Spigot is up to date ({current_version}).")
        return False, current_version, current_version

def check_geyser(stored_build):
    print("Checking for Geyser updates...")
    url = "https://download.geysermc.org/v2/projects/geyser/versions/latest/builds/latest"
    data = fetch_json(url)
    latest_build = data.get("build")
    version_str = data.get("version")
    jar_path = os.path.join(PLUGINS_DIR, "Geyser-Spigot.jar")

    needs_update = (latest_build != stored_build) or (not os.path.exists(jar_path))

    if needs_update:
        print(f"  -> Geyser update found: build #{stored_build} => build #{latest_build}")
        download_url = "https://download.geysermc.org/v2/projects/geyser/versions/latest/builds/latest/downloads/spigot"
        print(f"  -> Downloading Geyser to {jar_path}...")
        download_file(download_url, jar_path)
        return True, latest_build, version_str
    else:
        print(f"  -> Geyser is up to date (build #{stored_build}).")
        return False, stored_build, version_str

def check_floodgate(stored_build):
    print("Checking for Floodgate updates...")
    url = "https://download.geysermc.org/v2/projects/floodgate/versions/latest/builds/latest"
    data = fetch_json(url)
    latest_build = data.get("build")
    version_str = data.get("version")
    jar_path = os.path.join(PLUGINS_DIR, "floodgate.jar")

    needs_update = (latest_build != stored_build) or (not os.path.exists(jar_path))

    if needs_update:
        print(f"  -> Floodgate update found: build #{stored_build} => build #{latest_build}")
        download_url = "https://download.geysermc.org/v2/projects/floodgate/versions/latest/builds/latest/downloads/spigot"
        print(f"  -> Downloading Floodgate to {jar_path}...")
        download_file(download_url, jar_path)
        return True, latest_build, version_str
    else:
        print(f"  -> Floodgate is up to date (build #{stored_build}).")
        return False, stored_build, version_str

def main():
    versions = load_versions()
    changes = []

    spigot_updated, old_spigot, new_spigot = check_spigot()
    if spigot_updated:
        changes.append(f"Spigot {old_spigot} -> {new_spigot}")
        versions["spigot_version"] = new_spigot
    elif "spigot_version" not in versions and new_spigot:
        versions["spigot_version"] = new_spigot

    geyser_updated, new_geyser_build, geyser_ver = check_geyser(versions.get("geyser_build"))
    if geyser_updated:
        changes.append(f"Geyser v{geyser_ver} build #{new_geyser_build}")
        versions["geyser_build"] = new_geyser_build

    floodgate_updated, new_floodgate_build, floodgate_ver = check_floodgate(versions.get("floodgate_build"))
    if floodgate_updated:
        changes.append(f"Floodgate v{floodgate_ver} build #{new_floodgate_build}")
        versions["floodgate_build"] = new_floodgate_build

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
