# Aphasia Analysis Script

## Introduction
This is a project that takes text, turns it into audio, then utilizes OpenAIs' Realtime AI to producs audio and a transcript of the text as if spoken by someone with Aphasia. The ultimate goal of this project is to be used as a way to quickly test different prompts and eventually OpenAI realtime models for linguistic based accuracy to real people with various types of Aphasia. There could be great value to the world of sppech therapy in understanding how well AI can replicate PWAs as well as understand what their intended meaning and words are. This project is intended to build upon the Aphasiafier project by the BYU CS PCCL.

### How the script works
1. Reads in all files from a folder in /transcripts
2. Utilizes tts.py to convert all files into audio files
    1. These are stored under `/normal/<specified_folder>`
3. Audio files in /normal are sent through OpenAI Realtime w/ specified prompt in /prompts
    1. The results sre stored under /aphasia
4. The files in /aphasia/<folder_name> are then run through BatchAlign2 Transcription + Morphology
    1. The results are stored in /final as .cha transcripts. *Eval commands can be run on these files*

The reason for the complexity is due to our need to replicate specific research parameters. You will notice that a new websocket connection is opened per file when converting from normal to aphasia simulated audio. This is to remove the context window entirely as each file MUST be treated as a separate entity to simulate the indivudual nature of the human interviews in TalkBank. It is also vital to send audio rather than text through the Realtime API to simulate the actual usage of the aphasiafier tool which requires audio input.

## Approach to Using CLAN

The process to using the CLAN software is as follows:
1. Install it first 
2. Make sure to install the morphology library as well
Reference this book for guidance (start on page, #...)

You will need to process a basic text file of input sentences a few times to get the right output. The CLAN software expects a specific type of file called a .cha file. There are specific headers for this file type that need to be used in order for the software to process it correctly. Reference the CLAN book [here](www.google.com). There is a system developed by the AphasiaBank organization referred to as CHAT that defines the syntax for their transcript files [here](www.google.com) as well. This is the syntax you could use to markup punctuation and pauses for example in someone's Aphasia speech. That won't be necessary for this script but could be valuable in the future

#### Using CLAN

First, command CLAN to run morphology on your aphasia text in order to provide more holistic and accurate linguistic measurements.
The command should look similar to `mor  @ +t*PAR` if you use the GUI interface to build the command (recommended)
- The result of this command will be modifications to any .cha files you included as well as a .ulx.cex file specifying any words that the mor command could not recogonize as part of its dictionaries. These are most likely to be numbers, times, money, or quotations in your sentences. It's best if you go through the files and fix any of there errors then run mor again.

Second, now that you have your .cha files with morphology, you an run the EVAL command and produce a more complete result of lexical analysis.
- The command will look like `eval @ =t*PAR: +u +leng` if you only select the participant type when using the GUI. (recomended)

You should now have a spreadsheet generate as an output with a row for each .cha file you inserted into the EVAL command

For more information on the results of the EVAL command go to section 8.5.1 in [this manual.](https://talkbank.org/0info/manuals/CLAN.pdf)

#### **Using BatchAlign2**

Below are my personal notes and observations, but this link takes you to the developer's usage guide:

https://talkbank.org/0info/BA2-usage.pdf

It looks like the Word Error Rate (WER) when BatchAlign2 is used to generate a CHAT transcript from audio is very dependent on the quality of the recordings going into the system. It can vary from 1% to 20% when **REV-AI ** is used according to [this](https://journals.sagepub.com/doi/full/10.1177/09637214241304345#core-bibr14-09637214241304345-1) study, which used BatchALign2's built in benchmarking feature to test varying audio conditions on two-party interviews and TED speeches.

BatchAlign2 can also analyze CHAT transcripts for morphosyntactic structure. This is extremely accurate in english according to the same study above.

## Talk Bank & API Privacy

TalkBank requires that their data is not shared outside of the platform. This makes things a little tricky when utilizing AI APIs that could potentially collect data for training purposes. It looks like we are in the clear with OpenAI's API though according to their Terms and Conditions:

"Your data is your data. As of March 1, 2023, data sent to the OpenAI API is not used to train or improve OpenAI models (unless you explicitly opt in to share data with us).""
https://platform.openai.com/docs/guides/your-data

There are some caveats though such as

BatchAlign can be set up to utilize a local (I think?) Whisper1 model or REV AI. REV AI's API seems to be locked down but there is temporary storage involved. This shouldn't be too much of an issue since BatchALign2 is supported by the TAlkBank project.

##### Excluded from Batch EVAL
NEURAL-2 Other 
UMD bilingual


#### BatchAlign Process

AS of now one needs to do the following to run BatchAlign2
0. Run `batchalign setup` and add your RevAI API key
1. Add all .wav files to the input folder
2. Run `batchalign transcribe input output`
3. Run `batchalign morph output morph`
    You now have ASR based transcripts with morph tags in morph
4. Utililze CLAN to get NLP metrics in a spreadsheet

1. Run Script
2. Run BatchAlign transcribe on aphasia .wavs - HAVE TO BE .wav or .mp3
3. Run BatchAlign morphology on the output of step 2 or just use CLAN directly perhaps?
4. Run CLAN eval on output of step 3
5. Preform analysis on resultant spreadsheet    

### Pulling plaintext sentences from .cha files
1. Run `gem +s<Name_of group> +n +d <filenames> -t*INV`
2. Run `flo +t* <filenames>`

`+n` tells CLAN to only extract that section

`+d` tells CLAN to maintain acceptable CLAN format

`+/-t*` is where you specify speaker tier. If this breaks, just use the UI to EXCLUDE the INV tier instead of INCLUDE the PAR tier

### Flow of acquiring Transcripts

1. Start with ALL TalkBank data
2. Lose some on running gem 
    Some don't have the same gem name
    Some use an INV tier other than INV like OTH for example
3. flo_script only takes lines over 15 chars, some files only have lines under 15 chars