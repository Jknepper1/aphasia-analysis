# Source Locations

## Overview

There are multiple types of data flowing through this project in order to get the comparisons we need for the data analysis. This file contains a brief overview of how the data flows for each of these types from start to finish within the context of the aphasiafier pipeline. This is important to keep track of for future paper and to validate our process, ensuring it's legitimate. As well, modifications are made over time and multiple batches are pushed through the pipeline, so having this documentation ensures consistency and repeatability for the future.


## Process

All data types stem from the same directory and its subdirectories: `talkbank_sorted_HC` which is a collection of almost every transcript within the TalkBank Corpora, sorted by the `Group` metadata into their respective language types. This is done using the `transcript_sorted.py` script under `/helpers`, which is in this project to assit new users in filtering TalkBank for their own use.

    Talkbank transcripts cannot be provided with this project in order to maintain compliance with the TalkBank privacy policies. You must acquire those on your own.

The final step on each data type is running the `eval` command in the CLAN software on the resultant files. The output of this command is a spreadsheet containing natural language features per file. These metrics are can be averaged together and compared with the averages from the other data types.

### Human Coded Control

This is control files from talkbank. The transcripts are unaltered from their original human coded state. 

1. The filtered control folder is the base for this data
2. Desired gem is extracted from full transcripts:
    - Run `gem +s<name_of_section> +n +d <filenames> +t*PAR`
    - NOTE: This is a lossy process due to the fact that some transcripts title their gems slightly differently.
3. CLAN EVAL command is run manually on files:
    - Run `mor`
    - Run `eval`

### BatchAlign2 Control

This is the control files from TalkBank stripped of their human coding down to plaintext then processed through BatchAlign2 transcribe and morphotaging

1. The filtered control folder is the base for this data
2. Desired gem is extracted from full transcripts:
    - Run `gem +s<name_of_section> +n +d <filenames> +t*PAR`
3. Extracted section (gem) is converted into purely plaintext for tts processing
    - Run `flo +t* <filenames>`
    - Execute `flo_grab.py` on resultant files to pull only the %flo lines out of the `.cha` transcript
3. The sample size is then narrowed to 60 files to speed up processing:
    - Samples are randomly selected using `random_select.py` under `/helpers`
    - Random sample is stored in subfolder `src/transcripts/cont_<gem_type>/<gem_type>_cont_sample`
4. Sample set is then processed through BatchAlign2 ONLY
    - Run aphasiafier script with `--start-point` set to `3`
    - Option `3` runs tts and the BatchAlign2 pipeline while skipping any aphasiafication

### Aphasiafied w/ BatchAlign2 

This is the Aphasiafier data as processed through the entire pipeline as it stands. We may cycle out the BatchAlign2 Morphology step if it comes out that CLAN Mor tagging is superior.

1. A sample of 60 control files is utilized as the base for this data
2. Run the entire aphasiafier script on the 60 control files
    - Run script with `--start-point` set to `0`
3. Process output files in `/final` through CLAN EVAL command
    - Run `eval`

### Human Coded Aphasia

This is TalkBank data in its purset form. Human coded transcripts of the selected aphasia type, filtered by Gem (section)

1. Use the desired aphasia type folder under `talkbank_sorted_HC` as the base
2. Desired gem is extracted from full transcripts:
    - Run `gem +s<name_of_section> +n +d <filenames> +t*PAR`
    - NOTE: This is usually a lossy process because many corpora do not name their gems the same thing. If the sample sizes are big enough afterwards, then this is not a big problem.
3. CLAN EVAL command is run manually on files:
    - Run `mor`
    - Run `eval`


### BatchAlign2 Aphasia

Talkbank transcripts processed through BatchAlign2 without any aphasiafication added.

1. Use the desired aphasia type folder under `talkbank_sorted_HC` as base
2. Desired gem is extracted from full transcripts:
    - Run `gem +s<name_of_section> +n +d <filenames> +t*PAR`
3. Extracted section (gem) is converted into purely plaintext
    - Run `flo +t* <filenames>`
    - Execute `flo_grab.py` on resultant files to pull only the %flo lines out of the `.cha` transcript
4. Sample set is then processed through BatchAlign2 ONLY
    - Run aphasiafier script with `--start-point` set to `3`