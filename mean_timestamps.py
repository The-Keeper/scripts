import re
import statistics
from collections import Counter

def parse_timestamp(ts):
    """Convert timestamp string to total seconds"""
    ts = ts.strip()
    
    # Handle different timestamp formats
    if ':' in ts:
        parts = ts.split(':')
        if len(parts) == 2:  # mm:ss.ms
            minutes, seconds = parts
            hours = 0
        elif len(parts) == 3:  # hh:mm:ss.ms
            hours, minutes, seconds = parts
        else:
            raise ValueError(f"Invalid timestamp format: {ts}")
    else:
        raise ValueError(f"Invalid timestamp format: {ts}")
    
    # Split seconds and milliseconds
    if '.' in seconds:
        seconds, milliseconds = seconds.split('.')
        milliseconds = milliseconds.ljust(3, '0')  # Pad milliseconds to 3 digits
    else:
        milliseconds = 0
    
    return (int(hours) * 3600 + 
            int(minutes) * 60 + 
            int(seconds) + 
            int(milliseconds) / 1000)

def format_timestamp(seconds):
    """Convert seconds back to timestamp format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds_remaining = seconds % 60
    if hours > 0:
        return f"{hours:01d}:{minutes:02d}:{seconds_remaining:06.3f}"
    else:
        return f"{minutes:01d}:{seconds_remaining:06.3f}"

def read_timestamps_from_file(filename):
    """Read timestamps from file in format 'timestamp1 - timestamp2'"""
    scene_changes = []
    
    with open(filename, 'r') as file:
        for line_num, line in enumerate(file, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue  # Skip empty lines and comments
                
            # Match the format "timestamp - timestamp"
            match = re.match(r'(.+?)\s*-\s*(.+)', line)
            if match:
                ts1, ts2 = match.groups()
                try:
                    source1_ts = parse_timestamp(ts1)
                    source2_ts = parse_timestamp(ts2)
                    scene_changes.append((source1_ts, source2_ts))
                    print(f"Line {line_num}: {ts1} -> {source1_ts:.3f}s, {ts2} -> {source2_ts:.3f}s")
                except ValueError as e:
                    print(f"Error parsing line {line_num}: {line}")
                    print(f"  {e}")
            else:
                print(f"Invalid format on line {line_num}: {line}")
    
    return scene_changes

def analyze_sync_discrepancies(scene_changes):
    """Analyze sync discrepancies between audio sources"""
    
    delays = []
    
    print("\nScene Change Analysis:")
    print("=" * 60)
    
    for i, (source1_ts, source2_ts) in enumerate(scene_changes, 1):
        # Calculate delay (difference between source2 and source1)
        delay = source2_ts - source1_ts
        
        delays.append(delay)
        
        print(f"Scene {i}:")
        print(f"  Source 1: {format_timestamp(source1_ts)} ({source1_ts:.3f}s)")
        print(f"  Source 2: {format_timestamp(source2_ts)} ({source2_ts:.3f}s)")
        print(f"  Delay (Source2 - Source1): {delay:+.3f}s ({delay*1000:+.1f}ms)")
        
        if delay > 0:
            print(f"  → Source 2 is {delay:.3f}s LATER than Source 1")
        elif delay < 0:
            print(f"  → Source 2 is {abs(delay):.3f}s EARLIER than Source 1")
        else:
            print(f"  → Sources are perfectly synced")
        print()

    # Statistical analysis
    if delays:
        print("Sync Analysis Summary:")
        print("=" * 40)
        print(f"Total scenes analyzed: {len(delays)}")
        print()
        print(f"Mean delay: {statistics.mean(delays):.6f}s ({statistics.mean(delays)*1000:+.2f}ms)")
        print(f"Median delay: {statistics.median(delays):.6f}s ({statistics.median(delays)*1000:+.2f}ms)")
        
        if len(delays) > 1:
            print(f"Delay std dev: {statistics.stdev(delays):.6f}s ({statistics.stdev(delays)*1000:.2f}ms)")
        else:
            print(f"Delay std dev: N/A (only one data point)")
            
        print(f"Min delay: {min(delays):.6f}s ({min(delays)*1000:+.2f}ms)")
        print(f"Max delay: {max(delays):.6f}s ({max(delays)*1000:+.2f}ms)")
        print(f"Delay range: {max(delays) - min(delays):.6f}s ({(max(delays) - min(delays))*1000:.2f}ms)")
        
        # Delay distribution
        print(f"\nDelay Distribution:")
        delay_bins = {}
        for delay in delays:
            bin_key = round(delay * 1000)  # Bin by milliseconds
            delay_bins[bin_key] = delay_bins.get(bin_key, 0) + 1
        
        for bin_ms, count in sorted(delay_bins.items()):
            delay_sec = bin_ms / 1000
            print(f"  {delay_sec:+.3f}s ({bin_ms:+.0f}ms): {count} occurrence(s)")
        
        # Check for consistency
        if len(delays) > 1:
            if statistics.stdev(delays) < 0.001:  # Less than 1ms variation
                print(f"\n✓ Excellent sync consistency!")
            elif statistics.stdev(delays) < 0.01:  # Less than 10ms variation
                print(f"\n✓ Good sync consistency")
            else:
                print(f"\n⚠ Sync inconsistencies detected!")
            
            if statistics.stdev(delays) < 0.01:  # Less than 10ms variation
                print(f"Recommended constant offset: {statistics.mean(delays):.3f}s")
        else:
            print(f"\nRecommended offset: {delays[0]:.3f}s (based on single measurement)")
            
    else:
        print("No valid scene changes to analyze")

def main():
    filename = input("Enter the filename containing timestamps: ").strip()
    
    try:
        scene_changes = read_timestamps_from_file(filename)
        
        if not scene_changes:
            print("No valid timestamp pairs found in the file.")
            return
            
        analyze_sync_discrepancies(scene_changes)
        
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
    except Exception as e:
        print(f"Error: {e}")

# Alternative: Hardcode filename for quick testing
# if __name__ == "__main__":
#     scene_changes = read_timestamps_from_file("timestamps.txt")
#     analyze_sync_discrepancies(scene_changes)

if __name__ == "__main__":
    main()