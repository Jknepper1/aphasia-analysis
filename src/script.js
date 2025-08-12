import "dotenv/config";
import fs from "fs";
import path from "path";
import OpenAI from "openai";
import WebSocket from "ws";
import decodeAudio from 'audio-decode';
import wav from "wav"

// Prompt for Aphasia text is set here
const prompt = fs.readFileSync("./src/prompts/prompt1.txt").toString()
console.log(prompt)

// Initial TTS conversion for normal english sentences
async function getAudio(sentences, openai) {

    for (let i = 0; i < sentences.length; i++) {
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


// Helper functions for mp3 decoding *************************************************************************
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
// ********************************************************************************************************** //

export async function decodeMp3(fileNum) {
  console.log("mp3decode called")
    for (let i = 0; i < fileNum; i++) {
        const file = path.resolve(`./output/speech${i}.mp3`)
        const audioFile = fs.readFileSync(file);
        const audioBuffer = await decodeAudio(audioFile);
        const channelData = audioBuffer.getChannelData(0);
        const fullAudio = base64EncodeAudio(channelData);


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
        console.log(`sentence ${i}`)
        await ws.send(JSON.stringify(event));
        await ws.send(JSON.stringify({ type: "response.create"})) // This should trigger the building of a response object based upon the last message sent

        await new Promise(res => {resolveResponseDone = res})
    }
}

// Takes aphasia audio and converts to text
async function aphasiaToText(openai) {
  const files = fs.readdirSync("./aphasia");
  for (const file of files) {
    const transcription = await openai.audio.transcriptions.create({
    file: fs.createReadStream(file),
    model: "gpt-4o-transcribe"
    })

    console.log(transcription.text);
  }
};

// Websocket logic ************************************************************************************************************
const url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17";
const ws = new WebSocket(url, {
  headers: {
    "Authorization": "Bearer " + process.env.OPENAI_API_KEY,
    "OpenAI-Beta": "realtime=v1",
  }
});

ws.on("message", handleEvent);


ws.on("close", (code, reason) => {
  console.warn("WS closed:", code, reason?.toString());
});


ws.on("open", function open() {
  console.log("Connected to server."); 
});

let pcmChunks = [];
let resolveResponseDone;

function handleEvent(data) {
  const serverEvent = JSON.parse(data);

  if (serverEvent.type === "session.created") {
    console.log("Session created");
    ws.send(JSON.stringify({
      type: "session.update",
      session: {
        instructions: prompt // Prompt set by variable at top of file
      }
    }));
  }

  if (serverEvent.type === "session.updated") {
    console.log("Session updated!")
  }

  if (serverEvent.type === "response.audio.delta") {
    // Access Base64-encoded audio chunks
    pcmChunks.push(Buffer.from(serverEvent.delta, "base64"))
  }

  if (serverEvent.type === "response.audio.done") {
    const pcm = Buffer.concat(pcmChunks);
    pcmChunks = [];

    const writer = new wav.FileWriter(
      `./aphasia/processed-${Date.now()}.wav`,
      { channels: 1, sampleRate: 24000, bitDepth: 16 }
    );
    writer.write(pcm);
    writer.end(() => console.log("💾 assistant-XX.wav written"));

    if (resolveResponseDone) { resolveResponseDone(); resolveResponseDone = null; } // Wait for audio.done before decode loop continues
  }

  
}

// MAIN RUNNING LOGIC *****************************************************************************************
async function main() {

  // Initialized only once for speed
  const openai = new OpenAI({
        apiKey: process.env.OPENAI_API_KEY,
  });
  
  // Converts text file into an array of sentences
    const sentences = fs.readFileSync("./src/sentences.txt", "utf8").split("\r\n")
    console.log(sentences);
    await getAudio(sentences, openai);
    console.log("Sentences processed!")

    // Get the amount of files in the /output directory
    const files = fs.readdirSync("./output");
    const fileNum = files.length;

    // decodes mp3 data, sends to socket and receives aphasia text
    await decodeMp3(fileNum);

    // Converts aphasia .wavs into sentences and appends to a single file for NLP
    await aphasiaToText(openai);

}

// Init 
main();
