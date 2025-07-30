import "dotenv/config";
import fs from "fs";
import path from "path";
import OpenAI from "openai";

// Converts text file into an array of sentences
const sentences = fs.readFileSync("./src/sentences.txt", "utf8").split("\r\n")
console.log(sentences);

// Start timer to measure program run time
const start = Date.now();
sentences.forEach( async (s, index) =>  {
    const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
    });

    // Unique file name with index
    const speechFile = path.resolve(`./output/speech${index}.mp3`);

    // The data passed to the openai speech model
    const mp3 = await openai.audio.speech.create({
        model: "gpt-4o-mini-tts",
        voice: "alloy",
        input: s,
        instructions: "Speak in a cheerful and positive tone.",
    });

    // builds a buffer from the response from OpenAI
    const buffer = Buffer.from(await mp3.arrayBuffer());
    // Write the buffer to a file with the path in speechFile
    await fs.promises.writeFile(speechFile, buffer);
})