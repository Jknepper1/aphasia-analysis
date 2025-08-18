# Aphasia Analysis Script

## Introduction
This is a project that takes text, turns it into audio, then utilizes OpenAIs' Realtime AI to producs audio and a transcript of the text as if spoken by someone with Aphasia. The ultimate goal of this project is to be used as a way to quickly test different prompts and eventually OpenAI realtime models for linguistic based accuracy to real people with various types of Aphasia. There could be great value to the world of sppech therapy in understanding how well AI can replicate PWAs as well as understand what their intended meaning and words are. This project is intended to build upon the Aphasiafier project by the BYU CS department.

### How the script works



## Approach to Using CLAN

The process to using the CLAN software is as follows:
1. Install it first 
2. Make sure to install the morphology library as well
Reference this book for guidance (start on page, #...)

You will need to process a basic text file of input sentences a few times to get the right output. The CLAN software expects a specific type of file called a .cha file. There are specific headers for this file type that need to be used in order for the software to process it correctly. Reference the CLAN book [here](www.google.com). There is a system developed by the AphasiaBank organization referred to as CHAT that defines the syntax for their transcript files [here](www.google.com) as well. This is the syntax you could use to markup punctuation and pauses for example in someone's Aphasia speech. That won't be necessary for this script but could be valuable in the future

### From Input to Output
Input: .txt file of sentences (see the example set1.txt) - **Ensure there is no trailing newline in your file**
Aphasia.txt - After running the script you will have your aphasiafied sentences in a .txt file
CLAN formatting: The easiest way to convert your .txt file to a .cha file is by running it through AI. GPT-5 Does well. It is important to familarize yourself with the CLAN format so that you can confirm your file is set up properly in this step should you choose to use AI 

**Using CLAN**

First, command CLAN to run morphology on your aphasia text in order to provide more holistic and accurate linguistic measurements.
The command should look similar to `mor  @ +t*PAR` if you use the GUI interface to build the command (recommended)
- The result of this command will be modifications to any .cha files you included as well as a .ulx.cex file specifying any words that the mor command could not recogonize as part of its dictionaries. These are most likely to be numbers, times, money, or quotations in your sentences. It's best if you go through the files and fix any of there errors then run mor again.

Second, now that you have your .cha files with morphology, you an run the EVAL command and produce a more complete result of lexical analysis.
- The command will look like `eval @ =t*PAR: +u +leng` if you only select the participant type when using the GUI. (recomended)

You should now have a spreadsheet generate as an output with a row for each .cha file you inserted into the EVAL command