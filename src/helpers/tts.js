import fs from "fs";
import path from "path";

// Initial TTS conversion for normal english sentences
export async function getAudio(sentences, openai, outputDirName) {

    for (let i = 0; i < sentences.length; i++) {
        console.log(`Processing transcript number ${i}`);
        
        // Trim any invisible whitespace or carriage returns
        let cleanSentence = sentences[i].trim();

        // Clear filename from front delimit at :
        const filenameDelimiterIndex = cleanSentence.indexOf(":");
        if (filenameDelimiterIndex !== -1) {
            cleanSentence = cleanSentence.substring(filenameDelimiterIndex + 2).trim();
        }
        console.log(`Cleaned sentence: "${cleanSentence}"`);
    
        // 2. THE FIX: If the string is empty after trimming, skip it
        if (!cleanSentence) {
            console.log("Skipping empty line...");
            continue; 
        }

        // Unique file name with index
        const speechFile = path.resolve(`./normal/${outputDirName}/speech${i}.mp3`);

        // The data passed to the openai speech model
        const mp3 = await openai.audio.speech.create({
            model: "gpt-4o-mini-tts",
            voice: "alloy",
            input: cleanSentence,
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