"""
Release Manifest Generator
==========================
Compiles versions, commit hashes, dependencies, and file checksums into manifest files.
"""
import json
import datetime
import os
import subprocess


def generate_manifest() -> None:
    """
    Generates release_manifest.json describing the production release build properties.
    """
    version = "1.0.0"
    build_number = "104"
    commit_hash = "unknown"

    # Try retrieving current commit hash via git
    try:
        commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
    except Exception:
        pass

    manifest_data = {
        "version": version,
        "build_number": build_number,
        "commit_hash": commit_hash,
        "release_date": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "dependencies": {
            "backend": "requirements.txt",
            "frontend": "package.json"
        },
        "platforms_supported": ["Linux/AMD64", "Linux/ARM64", "Windows/AMD64"]
    }

    manifest_path = os.path.join(os.path.dirname(__file__), "release_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    print(f"Release manifest generated successfully at: {manifest_path}")


if __name__ == "__main__":
    generate_manifest()
