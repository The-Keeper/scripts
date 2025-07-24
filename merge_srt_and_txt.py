import argparse

def parse_srt(input_file):
    """Extracts subtitle blocks (number, timestamp, text) from an SRT file."""
    subtitles = []
    with open(input_file, 'r', encoding='utf-8') as f:
        blocks = f.read().strip().split('\n\n')  # Split by double newline
    for block in blocks:
        lines = block.split('\n')
        if len(lines) >= 3:  # Valid block: [number, timestamp, text...]
            num = lines[0]
            time = lines[1]
            text = '\n'.join(lines[2:])  # Handle multi-line subtitles
            subtitles.append((num, time, text))
    return subtitles

def parse_translation_txt(input_file):
    """Reads translated lines (one per subtitle) from a plain text file."""
    with open(input_file, 'r', encoding='utf-8') as f:
        translations = f.read().split('\n')
    return [t.strip() for t in translations if t.strip()]  # Remove empty lines

def merge_srt_with_translation(original_srt, translations, output_file):
    """Writes a new SRT file with original timestamps + translated text."""
    if len(original_srt) != len(translations):
        raise ValueError("Number of subtitles and translations do not match!")

    with open(output_file, 'w', encoding='utf-8') as f:
        for (num, time, _), translated_text in zip(original_srt, translations):
            f.write(f"{num}\n{time}\n{translated_text}\n\n")

if __name__ == "__main__":
    # Set up command-line argument parser
    parser = argparse.ArgumentParser(
        description="Merge translated text into an SRT file while preserving timestamps."
    )
    parser.add_argument(
        "--srt",
        required=True,
        help="Path to the original SRT file."
    )
    parser.add_argument(
        "--txt",
        required=True,
        help="Path to the translation TXT file (one line per subtitle)."
    )
    parser.add_argument(
        "--output",
        default="translated.srt",
        help="Path to the output SRT file (default: 'translated.srt')."
    )
    args = parser.parse_args()

    # Process files
    original_subtitles = parse_srt(args.srt)
    translations = parse_translation_txt(args.txt)

    try:
        merge_srt_with_translation(original_subtitles, translations, args.output)
        print(f"Success! Translated SRT saved to: {args.output}")
    except ValueError as e:
        print(f"Error: {e}")
