#!/usr/bin/env python3
import os
import subprocess
import shlex
import argparse
import json
from typing import List, Dict, Optional

def get_track_info(mkv_file: str) -> List[Dict]:
    """Get track info (ID, type, language) from an MKV file using mkvmerge."""
    tracks = []

    info_cmd = ["mkvmerge", "-J", mkv_file]
    result = subprocess.run(info_cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Error getting track info for {mkv_file}: {result.stderr}")
        return tracks

    try:
        data = json.loads(result.stdout)
        for track in data["tracks"]:
            track_id = track["id"]
            track_type = track["type"]
            language = track.get("properties", {}).get("language", "und")
        
            tracks.append({
                "id": track_id,
                "type": track_type,
                "language": language
            })
    except (json.JSONDecodeError, KeyError) as e:
        print(f"❌ Error parsing track info for {mkv_file}: {e}")

    return tracks

def remux_to_new_file(mkv_file: str, track_ids: List[int], dry_run: bool = False) -> bool:
    """Remux into a new file (with '-o new.mkv') excluding specified tracks."""
    out_dir = "out"
    os.makedirs(out_dir, exist_ok=True)
    output_file = os.path.join(out_dir, os.path.basename(mkv_file))

    # Build exclude tracks argument for all track types
    exclude_tracks = ",".join(f"{tid}" for tid in track_ids)

    cmd = ["mkvmerge", "-o", output_file, "--audio-tracks", f"!{exclude_tracks}", mkv_file]

    if dry_run:
        print(f"[DRY RUN] Would remux {mkv_file} to {output_file}, excluding tracks {track_ids}")
        print("COMMAND:")
        print(shlex.join(cmd))
        return True

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ Error remuxing {mkv_file}: {result.stderr}")
        return False
    else:
        print(f"✅ Created {output_file} (excluded tracks {track_ids})")
        return True

def process_files(directory: str, languages: List[str], dry_run: bool = False):
    """Process all MKV files in directory, removing audio tracks of specified languages."""
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(".mkv"):
                mkv_file = os.path.join(root, file)
                tracks = get_track_info(mkv_file)
                
                # Find tracks to remove (audio tracks matching any of the specified languages)
                tracks_to_remove = [
                    t["id"] for t in tracks
                    if t["type"] == "audio" and t["language"] in languages
                ]

                if not tracks_to_remove:
                    print(f"⚠️ No audio tracks in languages {languages} found in: {mkv_file}")
                    continue

                print(f"🔍 Found {len(tracks_to_remove)} tracks to remove in {mkv_file}: {tracks_to_remove}")
                remux_to_new_file(mkv_file, tracks_to_remove, dry_run)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Remove audio tracks of specified languages from MKV files."
    )
    parser.add_argument("directory", help="Directory containing MKV files")
    parser.add_argument("-l", "--languages", required=True, nargs="+", 
                       help="Language codes to exclude (e.g., 'eng', 'jpn', 'spa')")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Preview changes without modifying files")

    args = parser.parse_args()

    print(f"Processing directory: {args.directory}")
    print(f"Excluding languages: {args.languages}")
    print(f"Dry run: {args.dry_run}")

    process_files(args.directory, args.languages, args.dry_run)
