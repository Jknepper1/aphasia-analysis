
# Filter for lines starting with %flo:
# To get %flo on a .cha file, run FLO  @  +t* with @ representing whatever files you put in the CLAN 
# DO NOT USE +d on the flo command or else the %flo is removed and then the script will break
import os

def extract_flo_lines(file_path, filename):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    # TODO: Grab the file name and append it to  each line
    # Filter out sentences by @G category

    flo_lines = []  
    flo_lines.append("@:" + filename) # Add the filename at the beginning of the list of sentences for context
    for line in lines:
        if line.startswith('%flo:'):
            if line.startswith('%flo:'):
                # Clean the line: remove prefix, strip whitespace
                clean_content = line[len('%flo:'):].strip()
                
                # Requirement: only lines > 20 chars (excluding filename)
                if len(clean_content) > 20:
                    # Format: "filename: content"
                    flo_lines.append(clean_content)
        elif line.startswith('*INV'):
            exit(f"Error in {file_path}: The file is not fully excluded of INV tier, data may be skewed.")
    
    return flo_lines

def write_to_dir(sentences, output_file_path):
    with open(output_file_path, 'a', encoding='utf-8') as output_file:
        for sentence in sentences:
            output_file.write(sentence + '\n')
    output_file.close()

def main():
    flo_directory = input("Enter the path to the directory containing the .flo.cex files: ")
    subfolder = input("Enter subfolder of ./src/transcripts to store control files: ")
   
    directory = f"./src/transcripts/{subfolder}/"

    if not os.path.exists(directory):
        print(f"Directory {directory} not found. Creating it...")
        os.makedirs(directory, exist_ok=True)

    for file in os.listdir(flo_directory):
        in_directory = os.path.join(flo_directory, file)
        transcript = extract_flo_lines(in_directory, file)
        write_to_dir(transcript, directory + file.replace('.flo.cex', '.txt'))
    
    print("Done!")

if __name__ == "__main__":
    main()