import os
import random
import shutil
import sys

# Pick a specific seed in order to have reproducible steps for research paper
random.seed(2026)

if len(sys.argv) != 3:
    print("Usage: python random_select.py <input_dir_path> <output_path>")
    sys.exit(1)

dir_path = sys.argv[1]
out_path = sys.argv[2]

filenames = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))]

random_sample = random.sample(filenames, k=60)
total = 0

for i in random_sample:
    total +=1

print(f"Total files selected: {total}")

for i in random_sample:
    in_path = os.path.join(dir_path, i)
    shutil.copy2(in_path, out_path)





