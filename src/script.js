import "dotenv/config";
import fs from "fs";
import path from "path";
import OpenAI from "openai";
import { convertAudioToTranscript } from "./api.js"

// Converts text file into an array of sentences
const sentences = fs.readFileSync("./src/sentences.txt", "utf8").split("\r\n")
console.log(sentences);

// Start timer to measure program run time
async function getAudio() {
    for (let i = 0; i < sentences.length; i++) {
        const openai = new OpenAI({
        apiKey: process.env.OPENAI_API_KEY,
        });
        console.log(`Processing sentence number ${i}`);
        // Unique file name with index
        const speechFile = path.resolve(`./output/speech${i}.mp3`);

        // The data passed to the openai speech model
        const mp3 = await openai.audio.speech.create({
            model: "gpt-4o-mini-tts",
            voice: "alloy",
            input: sentences[i],
            instructions: "Speak in a normal and bland tone.",
        });

        // builds a buffer from the response from OpenAI
        const buffer = Buffer.from(await mp3.arrayBuffer());
        // Write the buffer to a file with the path in speechFile
        await fs.promises.writeFile(speechFile, buffer);

        // Adds delay to avoid rate limit issues when running large sets of sentences
        await new Promise((r) => setTimeout(r, 500));
    }
}

getAudio().then(convertAudioToTranscript);
