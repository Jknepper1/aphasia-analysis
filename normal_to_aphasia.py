import os
import json
import base64
import asyncio
import websockets
import wave

async def generate_aphasia_audio(prompt, api_key, normal_dir_name, aphasia_dir_name):
    # Setup directories
    print(f"Prompt accepted: {prompt}")
    input_dir = os.path.join(normal_dir_name)
    output_dir = os.path.join(aphasia_dir_name)
    os.makedirs(output_dir, exist_ok=True)

    url = "wss://api.openai.com/v1/realtime?model=gpt-realtime-mini-2025-12-15"
    headers = {"Authorization": f"Bearer {api_key}"}

    files = [f for f in os.listdir(input_dir) if f.endswith(".wav")]

    for i, filename in enumerate(files):
        print(f"\n[{i+1}/{len(files)}] Applying aphasia prompt to {filename}...")
        
        retry_count = 0
        max_retries = 3
        success = False
        
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)

        if os.path.exists(output_path):
            print(f"\n[{i+1}/{len(files)}] Skipping {filename} (Audio file already exists)...")
            continue

        while retry_count < max_retries and not success:
            try:
                # Open a FRESH connection for every file to ensure data isolation
                async with websockets.connect(url, additional_headers=headers, open_timeout=30) as ws:
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
                    elif update_event.get("type") == "error":
                        print(f"CRITICAL: API rejected the session update: {update_event['error']}")
                        break # Stop this file, something is wrong with the payload

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
                            print(event)
                            break
                            
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
                        
                    success = True
            except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed) as e:
                retry_count += 1
                wait_time = retry_count * 2
                print(f"Conn error on {filename}: {e}. Retrying in {wait_time}s... ({retry_count}/{max_retries})")
                await asyncio.sleep(wait_time)
            
            except Exception as e:
                print(f"Unexpected error on {filename}: {e}")
                break # Don't retry for logic errors