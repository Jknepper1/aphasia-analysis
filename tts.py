import os
import asyncio
import wave

async def generate_normal_audio(transcripts_dir, client, output_dir_name):
    output_dir = os.path.join(output_dir_name)
    os.makedirs(output_dir, exist_ok=True)

    files = [f for f in os.listdir(transcripts_dir) if f.endswith(".txt")]

    for filename in files:
        print(f"\n--- Processing Document: {filename} ---")
        file_path = os.path.join(transcripts_dir, filename)

        # Save the combined buffer as a single .wav file
        base_name = os.path.splitext(filename)[0]
        speech_file = os.path.join(output_dir, f"{base_name}.wav")
        
        if os.path.exists(speech_file):
            print(f"\n--- Skipping Document: {filename} (Audio file already exists) ---")
            continue
        
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()

        # This will hold the raw audio bytes for all 20 sentences
        combined_pcm_audio = bytearray()

        for i, line in enumerate(lines[1:]):
            clean_sentence = line.strip()

            print(f"  -> Requesting TTS for sentence {i+1}...")

            # Request raw PCM audio (uncompressed, headerless bytes)
            response = await client.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice="marin", # Recommended for quality by OpenAI
                input=clean_sentence,
                response_format="pcm" 
                # Add an instruction here to speak intentiaonally in a normal and flat tone for better audio to audio understanding
            )

            # Append this sentence's audio to our master buffer
            combined_pcm_audio.extend(response.content)

            # Delay to avoid rate limits
            await asyncio.sleep(0.5)

        # Skip saving if the file had no valid sentences
        if len(combined_pcm_audio) == 0:
            print(f"Skipping {filename}, no valid audio generated.")
            continue

        # Write the WAV file using Python's built-in wave library
        with wave.open(speech_file, "wb") as wav_file:
            wav_file.setnchannels(1)       # Mono
            wav_file.setsampwidth(2)       # 16-bit
            wav_file.setframerate(24000)   # OpenAI TTS sample rate
            wav_file.writeframes(combined_pcm_audio)

        print(f"Saved completed file: {speech_file}")