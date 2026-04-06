#!/bin/bash
cd /g/opensims_demo
git add GITHUB_RELEASE_INSTRUCTIONS.md RELEASE_NOTES_v1.0.0.md
git commit -m "docs: Add release notes for v1.0.0"
git push origin main
echo "=== 完成 ==="
