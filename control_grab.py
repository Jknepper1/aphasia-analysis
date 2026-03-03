
# Filter for lines starting with %flo:
# To get %flo on a .cha file, run FLO  @  +t* with @ representing whatever files you put in the CLAN 
# DO NOT USE +d on the flo command or else the %flo is removed and then the script will break
import os
import random

def random_sample(input_filepath, output_filepath, target_count=300):
    with open(input_filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Ensure we don't try to sample more lines than actually exist
    actual_target = min(target_count, len(lines))
    
    # Randomly pick unique lines
    sampled_lines = random.sample(lines, actual_target)
    
    with open(output_filepath, 'w', encoding='utf-8') as f:
        f.writelines(sampled_lines)
        
    print(f"Randomly extracted {len(sampled_lines)} sentences.")

def extract_flo_lines(file_path, filename):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    # TODO: Grab the file name and append it to the end of each line
    # Filter out sentences by @G category

    # Grab the 
    flo_lines = []  # Add the filename at the beginning of the list of sentences for context
    for line in lines:
        if line.startswith('%flo:'):
            # Extract the part after %flo: adds filename to front 
            flo_line = filename + ": " + line[len('%flo:'):].strip()
            if line.startswith('%flo:'):
                # Clean the line: remove prefix, strip whitespace
                clean_content = line[len('%flo:'):].strip()
                
                # Requirement: only lines > 20 chars (excluding filename)
                if len(clean_content) > 20:
                    # Format: "filename: content"
                    flo_lines.append(f"{filename}: {clean_content}")
        elif line.startswith('*INV'):
            exit(f"Error in {file_path}: The file is not fully excluded of INV tier, data may be skewed.")
    
    return flo_lines

def write_to_file(sentences, output_file_path):
    with open(output_file_path, 'a', encoding='utf-8') as output_file:
        for sentence in sentences:
            output_file.write(sentence + '\n')

def main():
    directory = input("Enter the path to the directory containing the .flo.cex files: ")
    sentences_file = input("Enter the path to the output sentences file (sentences will append to already present sentences): ")
    out_file = os.path.join("./src/sentences/", sentences_file)

    for file in os.listdir(directory):
        filename = os.path.join(directory, file)
        control_sentences = extract_flo_lines(filename, file)
        write_to_file(control_sentences, out_file)

    random_sample(out_file, "./src/sentences/300_random_important_event.txt")

if __name__ == "__main__":
    main()