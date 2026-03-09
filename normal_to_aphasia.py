import os
import json
import base64
import asyncio
import websockets
import wave

async def generate_aphasia_audio(prompt, api_key, normal_dir_name, aphasia_dir_name):
    # Setup directories
    input_dir = os.path.join(normal_dir_name)
    output_dir = os.path.join(aphasia_dir_name)
    os.makedirs(output_dir, exist_ok=True)

    url = "wss://api.openai.com/v1/realtime?model=gpt-realtime-2025-08-28"
    headers = {"Authorization": f"Bearer {api_key}"}

    files = [f for f in os.listdir(input_dir) if f.endswith(".wav")]

    for i, filename in enumerate(files):
        print(f"\n[{i+1}/{len(files)}] Applying aphasia prompt to {filename}...")
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)

        # Open a FRESH connection for every file to ensure data isolation
        async with websockets.connect(url, additional_headers=headers) as ws:
            # Wait for the server to confirm the session is ready
            initial_message = await ws.recv()
            initial_event = json.loads(initial_message)
            if initial_event.get("type") == "session.created":
                print("API session created.")
            
            # Configure the session
            await ws.send(json.dumps({
                "type": "session.update",
                "session": {
                    "type": "realtime",
                    "instructions": prompt,
                    "audio": {
                        "input": {
                            "format": {
                                "type": "audio/pcm",
                                "rate": 24000
                            },
                            "turn_detection": None # Manual turn detection moved here
                        },
                        "output": {
                            "format": {
                                "type": "audio/pcm",
                                "rate": 24000
                            }
                        }
                    }
                }
            }))
            update_message = await ws.recv()
            update_event = json.loads(update_message)
            if update_event.get("type") == "session.updated":
                print("Session updated with prompt, continuing...")

            # 3. Read the WAV file using python library to prevent clipping and static
            with wave.open(input_path, "rb") as wav_file:
                raw_audio = wav_file.readframes(wav_file.getnframes())
            
            audio_b64 = base64.b64encode(raw_audio).decode("utf-8") # has to be done for OpenAI API

            # 4. Send the audio
            await ws.send(json.dumps({
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_audio", "audio": audio_b64}]
                }
            }))

            # 5. Trigger the AI to respond
            await ws.send(json.dumps({"type": "response.create"}))

            # 6. Await and collect the streamed response
            audio_buffer = bytearray()
            
            async for message in ws:
                event = json.loads(message)
                
                if event["type"] == "response.output_audio.delta":
                    audio_buffer.extend(base64.b64decode(event["delta"]))
                    
                elif event["type"] == "response.done":
                    break # This cleanly exits the listener loop!
                    
                elif event["type"] == "error":
                    print(f"API Error on {filename}: {event}")
                    break

            # 7. Save the processed audio as a valid WAV
            if len(audio_buffer) > 0:
                with wave.open(output_path, "wb") as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(24000)
                    wav_file.writeframes(audio_buffer)
                print(f"Saved processed audio: {output_path}")
                
            # A short delay to prevent slamming the API rate limits
            await asyncio.sleep(0.5)