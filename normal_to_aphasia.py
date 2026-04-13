import base64
import json
import asyncio
import logging
import os
import wave

import websockets

logger = logging.getLogger(__name__)


async def generate_aphasia_audio(prompt, api_key, normal_dir_name, aphasia_dir_name):
    input_dir = os.path.join(normal_dir_name)
    output_dir = os.path.join(aphasia_dir_name)
    os.makedirs(output_dir, exist_ok=True)

    if not os.path.isdir(input_dir):
        raise FileNotFoundError(f"Normal audio directory not found: {input_dir}")

    files = sorted([f for f in os.listdir(input_dir) if f.endswith(".wav")])
    if not files:
        logger.warning("No WAV files found in normal audio folder: %s", input_dir)
        return

    url = "wss://api.openai.com/v1/realtime?model=gpt-realtime-mini-2025-12-15"
    headers = {"Authorization": f"Bearer {api_key}"}

    for i, filename in enumerate(files, start=1):
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)

        if os.path.exists(output_path):
            logger.info("Skipping existing aphasia audio: %s", output_path)
            continue

        logger.info("Processing file %s (%s/%s)", filename, i, len(files))
        retry_count = 0
        max_retries = 3
        success = False

        while retry_count < max_retries and not success:
            try:
                async with websockets.connect(url, additional_headers=headers, open_timeout=30) as ws:
                    initial_message = await ws.recv()
                    initial_event = json.loads(initial_message)
                    if initial_event.get("type") == "session.created":
                        logger.debug("Realtime session created for %s", filename)

                    await ws.send(
                        json.dumps(
                            {
                                "type": "session.update",
                                "session": {
                                    "type": "realtime",
                                    "instructions": prompt,
                                    "audio": {
                                        "input": {
                                            "format": {
                                                "type": "audio/pcm",
                                                "rate": 24000,
                                            },
                                            "turn_detection": None,
                                        },
                                        "output": {
                                            "format": {
                                                "type": "audio/pcm",
                                                "rate": 24000,
                                            }
                                        },
                                    },
                                },
                            }
                        )
                    )

                    update_message = await ws.recv()
                    update_event = json.loads(update_message)
                    if update_event.get("type") == "session.updated":
                        logger.debug("Session updated successfully for %s", filename)
                    elif update_event.get("type") == "error":
                        logger.error(
                            "Realtime session update rejected for %s: %s",
                            filename,
                            update_event.get("error"),
                        )
                        break

                    with wave.open(input_path, "rb") as wav_file:
                        raw_audio = wav_file.readframes(wav_file.getnframes())

                    audio_b64 = base64.b64encode(raw_audio).decode("utf-8")

                    await ws.send(
                        json.dumps(
                            {
                                "type": "conversation.item.create",
                                "item": {
                                    "type": "message",
                                    "role": "user",
                                    "content": [{"type": "input_audio", "audio": audio_b64}],
                                },
                            }
                        )
                    )

                    await ws.send(json.dumps({"type": "response.create"}))

                    audio_buffer = bytearray()
                    async for message in ws:
                        event = json.loads(message)
                        if event.get("type") == "response.output_audio.delta":
                            audio_buffer.extend(base64.b64decode(event["delta"]))
                        elif event.get("type") == "response.done":
                            logger.debug("Response complete for %s", filename)
                            break
                        elif event.get("type") == "error":
                            logger.error("API error for %s: %s", filename, event)
                            break

                    if audio_buffer:
                        with wave.open(output_path, "wb") as wav_file:
                            wav_file.setnchannels(1)
                            wav_file.setsampwidth(2)
                            wav_file.setframerate(24000)
                            wav_file.writeframes(audio_buffer)
                        logger.info("Saved processed aphasia audio: %s", output_path)
                    else:
                        logger.warning("No audio output produced for %s", filename)

                    success = True
            except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed) as exc:
                retry_count += 1
                wait_time = retry_count * 2
                logger.warning(
                    "Connection issue for %s on attempt %s/%s: %s",
                    filename,
                    retry_count,
                    max_retries,
                    exc,
                )
                if retry_count < max_retries:
                    await asyncio.sleep(wait_time)
            except Exception as exc:
                logger.exception("Unexpected error while processing %s", filename)
                break

        if not success:
            logger.warning("Failed to process %s after %s attempts.", filename, max_retries)
