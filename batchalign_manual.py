import os
import batchalign as ba

print("\nLoading Batchalign Pipeline...")
rev = ba.RevEngine(lang="eng", num_speakers=1)
morphosyntax = ba.StanzaEngine()
nlp = ba.BatchalignPipeline(rev, morphosyntax)

def transcribe_morphotag(aphasia_dir_name, output_dir_name):
    # Setup directories
    input_dir = os.path.join(aphasia_dir_name)
    output_dir = os.path.join(output_dir_name)
    # os.makedirs(output_dir, exist_ok=True)
    
    files = [f for f in os.listdir(input_dir) if f.endswith(".wav")]
    
    if not files:
        print(f"No WAV files found in {input_dir} to transcribe.")
        return

    for i, filename in enumerate(files):
        print(f"\n[{i+1}/{len(files)}] Transcribing {filename} to CLAN format...")
        input_path = os.path.join(input_dir, filename)
        
        # Swap the .wav extension for the TalkBank .cha extension
        base_name = os.path.splitext(filename)[0]
        output_path = os.path.join(output_dir, f"{base_name}.cha")
        
        try:
            # 1. Load the audio file into a Batchalign Document
            doc = ba.Document.new(media_path=input_path, lang="eng")
            
            # 2. Run the ASR pipeline
            doc = nlp(doc)
            
            # 3. Convert the generated document to a CLAN / CHAT file format
            chat = ba.CHATFile(doc=doc)
            
            # 4. Write it to the disk
            chat.write(output_path)
            print(f"Saved CLAN transcript: {output_path}")
            
        except Exception as e:
            print(f"Failed to transcribe {filename}. Error: {e}")