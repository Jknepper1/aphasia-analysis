import asyncio
import logging
import os
import wave

logger = logging.getLogger(__name__)


async def request_tts_audio(client, text, retries=3, delay=2.0):
    for attempt in range(1, retries + 1):
        try:
            response = await client.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice="marin",
                input=text,
                response_format="pcm",
            )
            return response.content
        except Exception as exc:
            logger.warning(
                "TTS request failed on attempt %s/%s: %s",
                attempt,
                retries,
                exc,
            )
            if attempt == retries:
                raise
            await asyncio.sleep(delay * attempt)


async def generate_normal_audio(transcripts_dir, client, output_dir_name):
    output_dir = os.path.join(output_dir_name)
    os.makedirs(output_dir, exist_ok=True)

    files = sorted([f for f in os.listdir(transcripts_dir) if f.endswith(".txt")])
    if not files:
        logger.warning("No .txt files found in transcript folder: %s", transcripts_dir)
        return

    for filename in files:
        file_path = os.path.join(transcripts_dir, filename)
        base_name = os.path.splitext(filename)[0]
        speech_file = os.path.join(output_dir, f"{base_name}.wav")

        if os.path.exists(speech_file):
            logger.info("Skipping existing audio file: %s", speech_file)
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()

        if not lines:
            logger.warning("Skipping empty transcript file: %s", file_path)
            continue

        combined_pcm_audio = bytearray()
        file_failed = False

        for i, line in enumerate(lines, start=1):
            clean_sentence = line.strip()
            if not clean_sentence:
                logger.debug("Skipping blank line %s in %s", i, filename)
                continue

            logger.info("Requesting TTS for sentence %s of %s", i, filename)
            try:
                fragment = await request_tts_audio(client, clean_sentence)
                combined_pcm_audio.extend(fragment)
            except Exception as exc:
                logger.error(
                    "Failed to generate TTS for %s sentence %s: %s",
                    filename,
                    i,
                    exc,
                )
                file_failed = True
                break

            await asyncio.sleep(0.5)

        if file_failed or len(combined_pcm_audio) == 0:
            logger.warning("Skipping file due to previous errors: %s", filename)
            continue

        with wave.open(speech_file, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(24000)
            wav_file.writeframes(combined_pcm_audio)

        logger.info("Saved completed file: %s", speech_file)
