import os
import random
import shutil

# Pick a specific seed in order to have reproducible steps for research paper
random.seed(2026)

dir_path = input("Pick dir path to randomly select transcripts from: ")

filenames = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))]

random_sample = random.sample(filenames, k=60)

for i in random_sample:
    print(i)

for i in random_sample:
    in_path = os.path.join(dir_path, i)
    out_path  =  os.path.join("..", "src", "transcripts", "ano_cinderella/ano_cinderella_sample")
    shutil.copy2(in_path, out_path)





