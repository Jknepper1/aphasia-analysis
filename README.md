# Aphasia Analysis Script

## Introduction
This is a project that takes text, turns it into audio, then utilizes OpenAIs' Realtime AI to producs audio and a transcript of the text as if spoken by someone with Aphasia. The ultimate goal of this project is to be used as a way to quickly test different prompts and eventually OpenAI realtime models for linguistic based accuracy to real people with various types of Aphasia. There could be great value to the world of sppech therapy in understanding how well AI can replicate PWAs as well as understand what their intended meaning and words are. This project is intended to build upon the Aphasiafier project by the BYU CS department.

### How the script works
1. Reads in a text prompt from /prompts
2. Takes a list of sentences from /sentences
    1. Calls TTS with a normal tone fore each sentence (Each input must be separated by a newline w/ no trailing newline at the end of the file)
    2. Saves the result to an mp3 in /output
3. Helper functions prepare audio to be processed by Realtime API
4. Sends audio to Realtime API through WebSocket connection
    1. Responses are saved as .wav files in /aphasia
5. Converts Aphasia audio from Realtime API back to text **(This will replaced with BatchALign2 conversion straight to CHAT)**
    1. Calls STT model from OpenAI for each .wav file
    2. First line overwrites then the file is appended to

You can input sentence sets, aphasia prompts, and specify an output directory 

## Approach to Using CLAN

The process to using the CLAN software is as follows:
1. Install it first 
2. Make sure to install the morphology library as well
Reference this book for guidance (start on page, #...)

You will need to process a basic text file of input sentences a few times to get the right output. The CLAN software expects a specific type of file called a .cha file. There are specific headers for this file type that need to be used in order for the software to process it correctly. Reference the CLAN book [here](www.google.com). There is a system developed by the AphasiaBank organization referred to as CHAT that defines the syntax for their transcript files [here](www.google.com) as well. This is the syntax you could use to markup punctuation and pauses for example in someone's Aphasia speech. That won't be necessary for this script but could be valuable in the future

### From Input to Output
Input: .txt file of sentences (see the example set1.txt) - **Ensure there is no trailing newline in your file**
Aphasia.txt - After running the script you will have your aphasiafied sentences in a .txt file
CLAN formatting: The easiest way to convert your .txt file to a .cha file is by using ReGex to add *PAR to the beginning of each line. You can also use AI. GPT-5 Does well. It is important to familarize yourself with the CLAN format so that you can confirm your file is set up properly in this step should you choose to use AI 

#### **Using CLAN**

First, command CLAN to run morphology on your aphasia text in order to provide more holistic and accurate linguistic measurements.
The command should look similar to `mor  @ +t*PAR` if you use the GUI interface to build the command (recommended)
- The result of this command will be modifications to any .cha files you included as well as a .ulx.cex file specifying any words that the mor command could not recogonize as part of its dictionaries. These are most likely to be numbers, times, money, or quotations in your sentences. It's best if you go through the files and fix any of there errors then run mor again.

Second, now that you have your .cha files with morphology, you an run the EVAL command and produce a more complete result of lexical analysis.
- The command will look like `eval @ =t*PAR: +u +leng` if you only select the participant type when using the GUI. (recomended)

You should now have a spreadsheet generate as an output with a row for each .cha file you inserted into the EVAL command

For more information on the results of the EVAL command go to section 8.5.1 in [this manual.](https://talkbank.org/0info/manuals/CLAN.pdf)

#### **Using BatchAlign2**

It looks like the Word Error Rate (WER) when BatchAlign2 is used to generate a CHAT transcript from audio is very dependent on the quality of the recordings going into the system. It can vary from 1% to 20% when **REV-AI ** is used according to [this](https://journals.sagepub.com/doi/full/10.1177/09637214241304345#core-bibr14-09637214241304345-1) study, which used BatchALign2's built in benchmarking feature to test varying audio conditions on two-party iterviews and TED speeches.

BatchAlign2 can also analyze CHAT transcripts for morphosyntactic structure. This is extremely accurate in english according to the same study above.

##### What is the difference between a batchalign2 analysis and a CLAN mor -> eval pipeline?

I asked this to chat and here's the summary points:

```
Why both exist / when to use each

BatchAlign2 + Stanza: Good for initial processing (turning audio → transcript → UD parse). Fast, modern, and multilingual.

CLAN mor + eval: Good for standardized analysis in CHAT/TalkBank corpora. This is what gives you continuity with decades of prior research and published norms.

So in practice, many researchers use BatchAlign2 for transcription/segmentation/alignment, then still run mor and eval in CLAN to get the standardized %mor tier and developmental profiles that can be compared across studies.
```

## Talk Bank & API Privacy

TalkBank requires that their data is not shared outside of the platform. This makes things a little tricky when utilizing AI APIs that could potentially collect data for training purposes. It looks like we are in the clear with OpenAI's API though according to their Terms and Conditions:

"Your data is your data. As of March 1, 2023, data sent to the OpenAI API is not used to train or improve OpenAI models (unless you explicitly opt in to share data with us).""
https://platform.openai.com/docs/guides/your-data

There are some caveats though such as

BatchAlign can be set up to utilize a local (I think?) Whisper1 model or REV AI. REV AI's API seems to be locked down but there is temporary storage involved. This shouldn't be too much of an issue since BatchALign2 is supported by the TAlkBank project.

