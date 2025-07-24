import json
import subprocess
import os
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

def select_chapters(chapters):
    """Display chapters and let user select which to include"""
    print("\nAvailable Chapters:")
    for i, chapter in enumerate(chapters, 1):
        start = chapter['start_time']
        end = chapter['end_time']
        duration = end - start
        print(f"{i}. {chapter['title']} ({format_time(start)} - {format_time(end)}, duration: {format_time(duration)})")
    
    selections = input("\nEnter chapter numbers to include (comma separated, e.g. 1,3,5): ")
    selected_indices = [int(num.strip()) - 1 for num in selections.split(",") if num.strip().isdigit()]
    
    return [chapters[i] for i in selected_indices]

def format_time(seconds):
    """Convert seconds to HH:MM:SS format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"

def seconds_to_timestamp(seconds):
    """Convert seconds to FFmpeg timestamp format (HH:MM:SS.MMM)"""
    td = timedelta(seconds=seconds)
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = td.microseconds // 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"

def create_ffmpeg_metadata_file(selected_chapters):
    """Create FFmpeg metadata file with chapters"""
    metadata_content = ";FFMETADATA1\n"
    
    cumulative_time = 0.0
    for i, chapter in enumerate(selected_chapters, 1):
        start_time = cumulative_time
        duration = chapter['end_time'] - chapter['start_time']
        end_time = start_time + duration
        
        metadata_content += f"""
[CHAPTER]
TIMEBASE=1/1000
START={int(start_time * 1000)}
END={int(end_time * 1000)}
title={chapter['title']}
"""
        cumulative_time = end_time
    
    # Create temporary metadata file
    metadata_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
    metadata_file.write(metadata_content)
    metadata_file.close()
    return metadata_file.name

def create_ffmpeg_concat_file(selected_chapters, input_file):
    """Create FFmpeg concat list file with absolute paths"""
    concat_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
    
    # Use absolute path to ensure FFmpeg can find the file
    abs_input_path = os.path.abspath(input_file)
    
    for chapter in selected_chapters:
        start = chapter['start_time']
        end = chapter['end_time']
        concat_file.write(f"file '{abs_input_path}'\n")  # ← Absolute path here
        concat_file.write(f"inpoint {start}\n")
        concat_file.write(f"outpoint {end}\n")
    
    concat_file.close()
    return concat_file.name

def main():
    # Find audio and JSON files in current directory
    audio_extensions = ('.mp3', '.m4a', '.opus', '.flac', '.wav', '.ogg', '.aac')
    audio_files = [f for f in os.listdir() if f.lower().endswith(audio_extensions)]
    json_files = [f for f in os.listdir() if f.endswith('.info.json')]
    
    if not audio_files or not json_files:
        print("No audio or JSON files found in current directory.")
        return
    
    audio_file = audio_files[0]
    json_file = json_files[0]
    
    print(f"Found audio file: {audio_file}")
    print(f"Found JSON file: {json_file}")
    
    # Load JSON data
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if 'chapters' not in data or not data['chapters']:
        print("No chapters found in the JSON file.")
        return
    
    # Prepare chapters list with times in seconds
    chapters = []
    for chapter in data['chapters']:
        chapters.append({
            'title': chapter['title'],
            'start_time': float(chapter['start_time']),
            'end_time': float(chapter['end_time'])
        })
    
    # Let user select chapters
    selected_chapters = select_chapters(chapters)
    if not selected_chapters:
        print("No chapters selected.")
        return
    
    # Generate output filename
    input_stem = Path(audio_file).stem
    output_file = f"concat_{input_stem}.mka"  # Using mka for better metadata support
    
    # Create temporary files
    concat_list_file = create_ffmpeg_concat_file(selected_chapters, audio_file)
    metadata_file = create_ffmpeg_metadata_file(selected_chapters)
    
    # Build FFmpeg command
    cmd = [
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',
        '-i', concat_list_file,
        '-i', metadata_file,
        '-map_metadata', '1',
        '-c', 'copy',
        output_file
    ]
    
    print("\nRunning FFmpeg command:")
    print(' '.join(cmd))
    
    # Run FFmpeg
    try:
        subprocess.run(cmd, check=True)
        print(f"\nSuccessfully created concatenated audio with chapters: {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"\nError running FFmpeg: {e}")
    except FileNotFoundError:
        print("\nFFmpeg not found. Please ensure FFmpeg is installed and in your PATH.")
    finally:
        # Clean up temporary files
        for f in [concat_list_file, metadata_file]:
            try:
                os.remove(f)
            except:
                pass

if __name__ == "__main__":
    main()