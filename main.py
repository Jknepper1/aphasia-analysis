import os
import asyncio
from dotenv import load_dotenv
from openai import AsyncOpenAI
#from audio_utils import save_as_wav, encode_audio
from batchalign_manual import transcribe_morphotag
from normal_to_aphasia import generate_aphasia_audio
from tts import generate_normal_audio

def setup():
    # 1. Initial check and creation
    # exist_ok=True replaces the need for `if (!fs.existsSync...)`
    os.makedirs("normal", exist_ok=True)
    os.makedirs("aphasia", exist_ok=True)
    os.makedirs("final", exist_ok=True)

    normal_files = os.listdir("normal")
    aphasia_files = os.listdir("aphasia")
    final_files = os.listdir("final")

    # 2. Wipe files prompt
    if normal_files or aphasia_files or final_files:
        # Python's built-in input() replaces the entire Node.js readline module
        ans = input("ERROR: Normal audio and/or aphasia directories already contain files... would you like to wipe files? BROKEN JUST PUT NO[Y/n]\n")
        
        if ans.lower() == 'y':
            # delete files in output directories
            for file in normal_files:
                os.remove(os.path.join("normal", file))
            for file in aphasia_files:
                os.remove(os.path.join("aphasia", file))

    # 3. Get starting point
    start_point = input("Where would you like to start? [0: Beginning, 1: NormalToAphasia, 2: Transcription]\n")
    
    # 4. Aphasiafier prompt loading loop
    prompt = ""
    while True:
        file_name = input("Input the name of your aphasiafier prompt in /src/prompts/: ")
        prompt_path = os.path.join(".", "src", "prompts", file_name)
        
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                prompt = f.read()
            print(f"The full path to the prompt is {prompt_path}")
            break
        except FileNotFoundError:
            print(f"File '{prompt_path}' not found, try again...")
            continue

    # 5. Setting Transcript Directory location
    transcripts_dir = ""
    while True:
        dir_name = input("Input a set of transcripts from /src/transcripts/: ")
        transcripts_dir = os.path.join(".", "src", "transcripts", dir_name)
        
        # Check if it actually exists and is a directory
        if not os.path.isdir(transcripts_dir):
            print(f"Directory '{transcripts_dir}' not found. Please try again.")
            continue 

        # Check if the directory is empty
        # os.listdir() returns a list of files. An empty list evaluates to False.
        if len(os.listdir(transcripts_dir)) == 0:
            print(f"Directory '{transcripts_dir}' exists but is empty! Please choose a folder with files.")
            continue 
            
        print(f"The set of transcripts to be aphasiafied is: {transcripts_dir}")
        break

    # 6. Target directories
    while True:
        dir_name = input("Input the name of your normal audio directory in /normal/: ")
        normal_dir = os.path.join(".", "normal", dir_name)
        
        if not os.path.isdir(normal_dir):
            print(f"Directory '{normal_dir}' not found. Please try again.")
            continue
        else:
            break

    while True:
        dir_name = input("Input the name of your aphasia audio directory in /aphasia/: ")
        aphasia_dir = os.path.join(".", "aphasia", dir_name)
        
        if not os.path.isdir(aphasia_dir): 
            print(f"Directory '{aphasia_dir}' not found. Please try again.")
            continue 
        else:
            break

    while True:
        dir_name = input("Input the name of your batchalign transcript directory in /final/: ")
        final_dir = os.path.join(".", "final", dir_name)
        
        if not os.path.isdir(aphasia_dir):
            print(f"Directory '{final_dir}' not found. Please try again.")
            continue 
        else:
            break
        
    # Return as a dictionary (similar to a JS object)
    return {
        "point": start_point, 
        "prompt": prompt, 
        "transcripts": transcripts_dir, 
        "normal_dir": normal_dir, 
        "aphasia_dir": aphasia_dir,
        "final_dir": final_dir
    }


async def main():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

    # Execute setup and grab the dictionary
    config = setup()
    
    # "Destructure" the dictionary variables
    point = config["point"]
    prompt = config["prompt"]
    transcripts = config["transcripts"]
    normal_dir = config["normal_dir"]
    aphasia_dir = config["aphasia_dir"]
    final_dir = config["final_dir"]

    client = AsyncOpenAI(api_key=api_key)

    # TTS
    if point == "0":
        print("TTS beginning...")
        await generate_normal_audio(transcripts, client, normal_dir)
        print("TTS ending...")

    # SpeechToSpeech
    if point == "0" or point == "1":
        print("Speech-to-Speech beginning...")
        await generate_aphasia_audio(prompt, api_key, normal_dir, aphasia_dir)
        print("Speech-to-Speech ending...")
    
    if point == "0" or point == "1" or point == "2":
        print("BatchAlign Transcription Beginning...")
        await transcribe_morphotag(aphasia_dir, final_dir)
        print("BatchAlign Transcription Ending...")


if __name__ == "__main__":
    asyncio.run(main())