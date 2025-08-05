import "dotenv/config";
import fsp from "fs/promises";
import fs from "fs";
import path from "path";
import OpenAI from "openai";
import WebSocket from "ws";
import decodeAudio from 'audio-decode';


async function getAudio(sentences) {
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

// Converts Float32Array of audio data to PCM16 ArrayBuffer
function floatTo16BitPCM(float32Array) {
  const buffer = new ArrayBuffer(float32Array.length * 2);
  const view = new DataView(buffer);
  let offset = 0;
  for (let i = 0; i < float32Array.length; i++, offset += 2) {
    let s = Math.max(-1, Math.min(1, float32Array[i]));
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
  }
  return buffer;
}

// Converts a Float32Array to base64-encoded PCM16 data
function base64EncodeAudio(float32Array) {
  const arrayBuffer = floatTo16BitPCM(float32Array);
  let binary = '';
  let bytes = new Uint8Array(arrayBuffer);
  const chunkSize = 0x8000; // 32KB chunk size
  for (let i = 0; i < bytes.length; i += chunkSize) {
    let chunk = bytes.subarray(i, i + chunkSize);
    binary += String.fromCharCode.apply(null, chunk);
  }
  return btoa(binary);
}

export async function decodeMp3(fileNum) {
    for (let i = 0; i < fileNum; i++) {
        const file = path.resolve(`./output/speech${i}.mp3`)
        console.log(file);
        const audioFile = await fsp.readFile(file);
        const audioBuffer = await decodeAudio(audioFile);
        const channelData = audioBuffer.getChannelData(0);
        const fullAudio = base64EncodeAudio(channelData);
        console.log(fullAudio); // This should just be straight data


        const event = {
            type: "conversation.item.create",
            item: {
                type: "message",
                role: "user",
                content: [
                    {
                        type: "input_audio",
                        audio: fullAudio,
                    },
                ],
            },
        };

        ws.send(JSON.stringify(event));
    }
}


// MAIN RUNNING LOGIC *****************************************************************************************

// Websocket logic
const url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17";
const ws = new WebSocket(url, {
  headers: {
    "Authorization": "Bearer " + process.env.OPENAI_API_KEY,
    "OpenAI-Beta": "realtime=v1",
  }
});

ws.on("open", function open() {
  console.log("Connected to server.");
});


function waitForOpenConnection(ws) {
  return new Promise((resolve) => {
    ws.on("open", resolve);
  });
}

async function main() {
    await waitForOpenConnection(ws); // Waits on the ws to open then resolves
    // Converts text file into an array of sentences
    const sentences = fs.readFileSync("./src/sentences.txt", "utf8").split("\r\n")
    console.log(sentences);
    await getAudio(sentences);

    // Get the amount of files in the /output directory
    const files= await fsp.readdir("./output");
    const fileNum = files.length;

    await decodeMp3(fileNum);

    ws.on("message", (e) => {
        console.log("Message from server", e.data)
    })
}

main();
