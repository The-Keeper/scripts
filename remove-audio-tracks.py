#!/usr/bin/env python3
import os
import subprocess
import shlex
import argparse
from typing import List, Dict, Optional

def get_track_info(mkv_file: str) -> List[Dict]:
    """Get track info (ID, type, language) from an MKV file using mkvmerge."""
    tracks = []

    info_cmd = ["mkvmerge", "-J", mkv_file]
    info_json = subprocess.run(info_cmd, capture_output=True, text=True).stdout
    import json
    try:
        data = json.loads(info_json)
        for track in data["tracks"]:
            track_id = track["id"]
            track_type = track["type"]
            language = track.get("properties", {}).get("language", "und")
        
            tracks.append({
                "id": track_id,
                "type": track_type,
                "language": language
            })
    except:
        pass

    return tracks

def delete_tracks_in_place(mkv_file: str, track_ids: List[int], dry_run: bool = False) -> bool:
    """Delete tracks in-place using mkvpropedit."""
    cmd = ["mkvpropedit", mkv_file] + [f"--delete-track={tid}" for tid in track_ids]

    if dry_run:
        print(f"[DRY RUN] Would delete tracks {track_ids} from {mkv_file} in-place")
        print("COMMAND:")
        print(shlex.join(cmd))
        return True

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ Error deleting tracks from {mkv_file}: {result.stderr}")
        return False
    else:
        print(f"✅ Removed tracks {track_ids} from: {mkv_file}")
        return True

def remux_to_new_file(mkv_file: str, track_ids: List[int], dry_run: bool = False) -> bool:
    """Remux into a new file (with '-o new.mkv') excluding specified tracks."""
    out_dir = "out"
    output_file = os.path.join(out_dir, os.path.basename(mkv_file))

    exclude_tracks = ",".join(f"!{tid}" for tid in track_ids)

    cmd = ["mkvmerge", "-o", output_file, "--audio-tracks", exclude_tracks, mkv_file]

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

def process_files(directory: str, language: str, in_place: bool, dry_run: bool = False):
    """Process all MKV files in directory, removing audio tracks of specified language."""
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(".mkv"):
                mkv_file = os.path.join(root, file)
                tracks = get_track_info(mkv_file)
                audio_tracks_to_remove = [
                    t["id"] for t in tracks
                    if t["type"] == "audio" and t["language"] == language
                ]

                if not audio_tracks_to_remove:
                    print(f"⚠️ No {language} audio tracks found in: {mkv_file}")
                    continue

                if in_place:
                    delete_tracks_in_place(mkv_file, audio_tracks_to_remove, dry_run)
                else:
                    remux_to_new_file(mkv_file, audio_tracks_to_remove, dry_run)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Remove audio tracks of a given language from MKV files."
    )
    parser.add_argument("directory", help="Directory containing MKV files")
    parser.add_argument("-l", "--language", required=True, help="Language code (e.g., 'eng', 'jpn')")
    parser.add_argument("--in-place", action="store_true", help="Edit files in-place (faster, uses mkvpropedit)")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without modifying files")

    args = parser.parse_args()

    process_files(args.directory, args.language, args.in_place, args.dry_run)
