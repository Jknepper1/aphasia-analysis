
# Filter for lines starting with %flo:
import os
import sys

def extract_flo_lines(file_path, filename):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    # TODO: Grab the file name and append it to  each line
    # Filter out sentences by @G category

    flo_lines = []  
    for line in lines[1::]: # Don't look at the @G first line. It's irrelevant
        if line.startswith('%flo:'):
            if line.startswith('%flo:'):
                # Clean the line: remove prefix, strip whitespace
                clean_content = line[len('%flo:'):].strip()
                
                # Requirement: only lines > 10 chars (excluding filename)
                if len(clean_content) > 10:
                    # Format: "filename: content"
                    flo_lines.append(clean_content)
        elif line.startswith('*INV') or line.startswith('*OTH'):
            print(f"Error in {file_path}: The file is not fully excluded of INV or OTH tier, data will be skewed. Not including")
            return []
    
    return flo_lines

def write_to_dir(sentences, output_file_path):
    with open(output_file_path, 'a', encoding='utf-8') as output_file:
        for sentence in sentences:
            output_file.write(sentence + '\n')
    output_file.close()

def main():
    if len(sys.argv) != 3:
        print("Usage: python flo_grab.py <flo_directory> <subfolder>")
        sys.exit(1)
    
    flo_directory = sys.argv[1]
    subfolder = sys.argv[2]
   
    directory = f"{subfolder}/"

    if not os.path.exists(directory):
        print(f"Directory {directory} not found. Creating it...")
        os.makedirs(directory, exist_ok=True)

    for file in os.listdir(flo_directory):
        in_directory = os.path.join(flo_directory, file)
        # if .flo NOT in file path, just skip <------------- This might solve some problems
        # Try and rubild broca_sandwich folder. Somewhere along the lines 130 ish files gets shrunk down to 52 and I think this script 
        # has something to do with it. The CLAN commands may as well.
        transcript = extract_flo_lines(in_directory, file)
        if len(transcript) > 2: # prevents all the random empty files from fluffing up directory
            write_to_dir(transcript, directory + file.replace('.flo.cex', '.txt'))
    
    print("Done!")

if __name__ == "__main__":
    main()