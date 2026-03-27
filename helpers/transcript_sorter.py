import os
import re
import subprocess
from pathlib import Path

CHAT_DIR = Path("../../talkbank_full_HC")
OUTPUT_DIR = Path(f"../src/transcripts/talkbank_sorted_HC") 


# The main use of this is to sort through the massive set of talkbank files and grab only the ones of a certain aphasia group type
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


def process_files():
    for cha_path in CHAT_DIR.rglob("*.cha"):
        base_name = cha_path.stem

        # 1. Grab the Aphasia Type
        aphasia_type = get_participant_group(cha_path)
        
        # 2. Create the specific subfolder for this group
        group_output_dir = OUTPUT_DIR / aphasia_type
        group_output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Processing {base_name} [{aphasia_type}]...")

        with open(cha_path, "r", encoding="utf-8") as f:
            data = f.read()

        safe_group_name = aphasia_type.replace(" ", "_").lower() # Just added this

        # Save directly into the new group-specific folder
        output_file = group_output_dir / f"{base_name}_{safe_group_name}.cha"

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(data)
    
        print(f"  -> Saved to {aphasia_type}/{output_file.name}")

if __name__ == "__main__":
    process_files()
    print(f"\nBatch processing complete! Files are sorted by diagnosis in {OUTPUT_DIR}.")