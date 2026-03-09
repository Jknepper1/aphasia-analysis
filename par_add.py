import re

def convert_to_cha(input_file, output_file):
    # Standard CHAT headers for AphasiaBank/CLAN
    headers = [
        "@UTF8",
        "@Begin",
        "@Languages:\teng",
        "@Participants:\tPAR Participant",
        "@ID:\teng|sample|PAR|||||Participant|||",
    ]
    
    footer = "@End"

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    with open(output_file, 'w', encoding='utf-8') as f:
        # Write the required headers
        for h in headers:
            f.write(h + "\n")
        
        for line in lines:
            clean_line = line.strip()
            if not clean_line:
                continue
            
            import re

            # ... inside your loop ...

            # 1. Remove all commas, they confuse the word count
            clean_line = clean_line.replace(',', '')

            # 2. Convert triple dots or dashes to single spaces
            clean_line = clean_line.replace('...', ' ').replace('-', ' ').replace('—', ' ').replace('_', ' ')

            # 4. Final Punctuation: Ensure EXACTLY one space before the final mark
            # and REMOVE any internal punctuation that isn't a word
            clean_line = re.sub(r'[^a-zA-Z0-9\s\.\!\?]', '', clean_line)
            clean_line = re.sub(r'([\.!\?])\s*$', r' \1', clean_line)
                
            # 1. Ensure space before punctuation (., !, ?) so MOR can read it
            # This regex finds punctuation at the end and ensures a space precedes it
            clean_line = re.sub(r'([\.!\?])\s*$', r' \1', clean_line)
            
            # 2. Append the Speaker Tier with the required Tab (\t)
            f.write(f"*PAR:\t{clean_line}\n")
        
        # Write the required footer
        f.write(footer + "\n")

# Usage
convert_to_cha('./src/aphasiaText/cinderella_wernicke_very_severe.txt', './test/cinderella_wernicke_batchalign.cha')
print("Conversion complete! You can now run 'mor' and 'eval' in CLAN.")