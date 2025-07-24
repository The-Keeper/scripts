import json
import subprocess
import os
from pathlib import Path

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

def create_ffmpeg_concat_file(selected_chapters, input_file, output_file):
    """Create FFmpeg concat command for audio segments"""
    
    # For audio-only processing, we'll use the concat demuxer approach which is more efficient
    # First create a temporary file listing the segments
    temp_file = "ffmpeg_concat_list.txt"
    
    with open(temp_file, 'w', encoding='utf-8') as f:
        for chapter in selected_chapters:
            start = chapter['start_time']
            end = chapter['end_time']
            duration = end - start
            f.write(f"file '{input_file}'\n")
            f.write(f"inpoint {start}\n")
            f.write(f"outpoint {end}\n")
            f.write(f"duration {duration}\n")
    
    # Build FFmpeg command
    cmd = [
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',
        '-i', temp_file,
        '-c', 'copy',  # Stream copy for no re-encoding
        output_file
    ]
    
    return cmd, temp_file

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
    output_file = f"concat_{input_stem}.{Path(audio_file).suffix[1:]}"
    
    # Create FFmpeg command
    cmd, temp_file = create_ffmpeg_concat_file(selected_chapters, audio_file, output_file)
    
    print("\nRunning FFmpeg command:")
    print(' '.join(cmd))
    
    # Run FFmpeg
    try:
        subprocess.run(cmd, check=True)
        print(f"\nSuccessfully created concatenated audio: {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"\nError running FFmpeg: {e}")
    except FileNotFoundError:
        print("\nFFmpeg not found. Please ensure FFmpeg is installed and in your PATH.")
    finally:
        # Clean up temporary file
        if os.path.exists(temp_file):
            os.remove(temp_file)

if __name__ == "__main__":
    main()
