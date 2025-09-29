import fs from "fs";
import path from "path";

// Initial TTS conversion for normal english sentences
export async function getAudio(sentences, openai, outputDir) {

    for (let i = 0; i < sentences.length; i++) {
        console.log(`Processing sentence number ${i}`);

        // Unique file name with index
        const speechFile = path.resolve(`./${outputDir}/speech${i}.mp3`);

        // The data passed to the openai speech model
        const mp3 = await openai.audio.speech.create({
            model: "gpt-4o-mini-tts",
            voice: "alloy",
            input: sentences[i],
            instructions: "Speak in a normal tone.",
        });

        // builds a buffer from the response from OpenAI
        const buffer = Buffer.from(await mp3.arrayBuffer());
        // Write the buffer to a file with the path in speechFile
        await fs.promises.writeFile(speechFile, buffer);

        // Adds delay to avoid rate limit issues when running large sets of sentences
        await new Promise((r) => setTimeout(r, 500));
    }
}