import os
import re
import subprocess
from pathlib import Path

# --- Configuration ---
CHAT_DIR = Path("./CHATtrans")
AUDIO_DIR = Path("./audioFiles")
TARGET_SECTION = input("What section would you like to pull? (e.g., Sandwich, Cinderella): ").strip()
OUTPUT_DIR = Path(f"./{TARGET_SECTION}") 

# --- Regex Patterns ---
TARGET_GEM_PATTERN = re.compile(rf'^@G:\s*{TARGET_SECTION}', re.IGNORECASE)
ANY_OTHER_GEM_PATTERN = re.compile(r'^@(G:|End)', re.IGNORECASE)
TIME_BULLET_PATTERN = re.compile(r'[\x15·](\d+)_(\d+)[\x15·]')

BUFFER_MS = 5000 

def get_participant_group(cha_file):
    """Parses the @ID header to find the participant's aphasia type."""
    with open(cha_file, 'r', encoding='utf-8') as f:
        for line in f:
            # Look for the Participant ID line
            if line.startswith('@ID:') and '|PAR|' in line:
                parts = line.split('|')
                # The group/diagnosis is the 6th field in TalkBank standard format
                if len(parts) > 5:
                    group = parts[5].strip()
                    # Clean the string to ensure it's a valid folder name
                    return "".join(c for c in group if c.isalnum())
            
            # Stop searching once the actual transcript dialogue begins
            if line.startswith('*'):
                break
                
    return "Unknown_Group"

def parse_cha_for_timestamps(cha_file):
    """Finds the start and end timestamps for the target @G: section."""
    start_ms = None
    end_ms = None
    in_target_section = False
    
    with open(cha_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not in_target_section:
                if TARGET_GEM_PATTERN.search(line):
                    in_target_section = True
                    continue 
            else:
                if ANY_OTHER_GEM_PATTERN.search(line):
                    break 
                
                match = TIME_BULLET_PATTERN.search(line)
                if match:
                    current_start = int(match.group(1))
                    current_end = int(match.group(2))
                    
                    if start_ms is None:
                        start_ms = current_start
                    end_ms = current_end 
                    
    return start_ms, end_ms

def find_matching_audio(base_name):
    """Finds the corresponding audio file, handling different extensions."""
    for ext in ['.wav', '.mp3', '.mp4', '.m4a']:
        audio_path = AUDIO_DIR / f"{base_name}{ext}"
        if audio_path.exists():
            return audio_path
    return None

def process_files():
    for cha_path in CHAT_DIR.rglob("*.cha"):
        base_name = cha_path.stem
        audio_path = find_matching_audio(base_name)
        
        if not audio_path:
            print(f"Skipping {base_name}: No matching audio file found.")
            continue
            
        # 1. Grab the Aphasia Type
        aphasia_type = get_participant_group(cha_path)
        
        # 2. Create the specific subfolder for this group
        group_output_dir = OUTPUT_DIR / aphasia_type
        group_output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Processing {base_name} [{aphasia_type}]...")
        
        # 3. Find timestamps
        start_ms, end_ms = parse_cha_for_timestamps(cha_path)
            
        if start_ms is None or end_ms is None:
            print(f"  -> '{TARGET_SECTION}' section not found. Skipping.")
            continue
            
        # 4. Math & Cropping
        start_sec = max(0, (start_ms - BUFFER_MS)) / 1000.0
        end_sec = (end_ms + BUFFER_MS) / 1000.0
        duration = end_sec - start_sec
        
        safe_section_name = TARGET_SECTION.replace(" ", "_").lower()
        # Save directly into the new group-specific folder
        output_file = group_output_dir / f"{base_name}_{safe_section_name}{audio_path.suffix}"
        
        command = [
            "ffmpeg", "-y", "-v", "error", 
            "-i", str(audio_path),
            "-ss", str(start_sec),
            "-t", str(duration),
            "-c", "copy", 
            str(output_file)
        ]
        
        subprocess.run(command)
        print(f"  -> Saved to {aphasia_type}/{output_file.name}")

if __name__ == "__main__":
    process_files()
    print(f"\nBatch processing complete! Files are sorted by diagnosis in {OUTPUT_DIR}.")