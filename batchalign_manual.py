import logging
import os

import batchalign as ba

logger = logging.getLogger(__name__)

logger.info("Loading BatchAlign pipeline...")
rev = ba.RevEngine(lang="eng", num_speakers=1)
morphosyntax = ba.StanzaEngine()
nlp = ba.BatchalignPipeline(rev, morphosyntax)

def transcribe_morphotag(aphasia_dir_name, output_dir_name):
    input_dir = os.path.join(aphasia_dir_name)
    output_dir = os.path.join(output_dir_name)
    os.makedirs(output_dir, exist_ok=True)

    files = sorted([f for f in os.listdir(input_dir) if f.endswith(".wav")])
    if not files:
        logger.warning("No WAV files found in %s to transcribe.", input_dir)
        return

    for i, filename in enumerate(files, start=1):
        input_path = os.path.join(input_dir, filename)
        base_name = os.path.splitext(filename)[0]
        output_path = os.path.join(output_dir, f"{base_name}.cha")

        logger.info("Transcribing %s (%s/%s)", filename, i, len(files))
        if os.path.exists(output_path):
            logger.info("Skipping existing transcript: %s", output_path)
            continue

        try:
            doc = ba.Document.new(media_path=input_path, lang="eng")
            doc = nlp(doc)
            chat = ba.CHATFile(doc=doc)
            chat.write(output_path)
            logger.info("Saved CLAN transcript: %s", output_path)
        except Exception as exc:
            logger.exception("Failed to transcribe %s", filename)
