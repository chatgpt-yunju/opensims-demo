#!/usr/bin/env python3
"""
Release upload script for OpenSims
- Commits pending changes (if any)
- Tags the current commit with version from version.json
- Pushes tag to remote
- Creates GitHub release and uploads assets
"""

import os
import json
import subprocess
import re
import sys
from pathlib import Path

def run_cmd(cmd, cwd=None):
    """Run command and return output"""
    print(f"$ {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERROR] {result.stderr}")
        raise RuntimeError(f"Command failed: {cmd}")
    return result.stdout.strip()

def main():
    project_dir = r"G:\opensims_demo"
    os.chdir(project_dir)
    print(f"[Info] Working in: {project_dir}")

    # Load version
    with open('version.json', 'r', encoding='utf-8') as f:
        ver_data = json.load(f)
    major = ver_data['major']
    minor = ver_data['minor']
    patch = ver_data['patch']
    build = ver_data['build']
    version = f"{major}.{minor}.{patch}.{build}"
    tag_name = f"v{version}"
    print(f"[Info] Version: {version}, Tag: {tag_name}")

    # Get current commit sha
    commit_sha = run_cmd("git rev-parse HEAD")
    print(f"[Info] Commit: {commit_sha}")

    # Check if tag already exists
    existing_tags = run_cmd("git tag -l").split()
    if tag_name in existing_tags:
        print(f"[Warn] Tag {tag_name} already exists. Skipping tag creation.")
    else:
        # Create annotated tag
        run_cmd(f'git tag -a "{tag_name}" -m "OpenSims {version}"')
        print(f"[OK] Created tag {tag_name}")

    # Push tag
    run_cmd(f"git push origin {tag_name}")
    print(f"[OK] Pushed tag {tag_name} to remote")

    # Extract token from remote URL
    remote_url = run_cmd("git config --get remote.origin.url")
    # pattern: https://<token>@github.com/owner/repo.git
    token_match = re.search(r'https://([^@]+)@', remote_url)
    if not token_match:
        print("[Error] Cannot extract token from remote URL. Make sure remote URL contains token.")
        sys.exit(1)
    token = token_match.group(1)
    # Extract owner/repo
    repo_match = re.search(r'github\.com/([^/]+)/([^./]+)', remote_url)
    if not repo_match:
        print("[Error] Cannot parse owner/repo from remote URL")
        sys.exit(1)
    owner, repo = repo_match.group(1), repo_match.group(2)
    print(f"[Info] Owner: {owner}, Repo: {repo}")

    # Prepare release notes
    release_name = f"OpenSims {version}"
    # Use changelog entry if available
    changelog_entries = ver_data.get('changelog', [])
    latest_entry = next((e for e in reversed(changelog_entries) if e['version'] == version), None)
    if latest_entry:
        body = f"{latest_entry['changes']}\n\nBuilt on: {ver_data.get('last_updated', 'unknown')}"
    else:
        body = f"OpenSims {version} release\n\nIncludes Human-like Chat System with 6 human traits.\nBuilt on: {ver_data.get('last_updated', 'unknown')}"

    # Create release via GitHub API
    import requests
    api_url = f"https://api.github.com/repos/{owner}/{repo}/releases"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "tag_name": tag_name,
        "target_commitish": commit_sha,
        "name": release_name,
        "body": body,
        "draft": False,
        "prerelease": False
    }
    print(f"[Info] Creating release {release_name}...")
    resp = requests.post(api_url, json=data, headers=headers)
    if resp.status_code not in (201, 200):
        print(f"[Error] Failed to create release: {resp.status_code} {resp.text}")
        sys.exit(1)
    release = resp.json()
    upload_url = release.get('upload_url')
    if not upload_url:
        print("[Error] No upload_url in release response")
        sys.exit(1)
    # Strip ? parameters
    upload_url = upload_url.split('{')[0]
    print(f"[OK] Release created: {release.get('html_url')}")

    # Assets to upload
    assets = [
        (f"dist/OpenSims_{version}.exe", "OpenSims executable (console)"),
        (f"OpenSims_v{version}_{datetime.now().strftime('%Y%m%d')}.zip", "Portable package")
    ]
    # Verify asset files exist
    for path, desc in assets:
        if not os.path.exists(path):
            print(f"[Warn] Asset not found: {path}. Skipping.")
            continue
        print(f"[Info] Uploading {desc}: {path}")
        with open(path, 'rb') as f:
            asset_data = f.read()
        # POST to upload URL with ?name=filename
        asset_url = f"{upload_url}?name={os.path.basename(path)}"
        resp = requests.post(asset_url, data=asset_data, headers={
            "Authorization": f"token {token}",
            "Content-Type": "application/octet-stream"
        })
        if resp.status_code not in (201, 200):
            print(f"[Error] Upload failed: {resp.status_code} {resp.text}")
        else:
            print(f"[OK] Uploaded {path}")

    print("\n" + "="*60)
    print(f"Release {release_name} published!")
    print(f"URL: {release.get('html_url')}")
    print("="*60)

if __name__ == "__main__":
    from datetime import datetime
    main()
