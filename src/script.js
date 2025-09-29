import "dotenv/config";
import fs from "fs"; // Could be cut
import path from "path"; // Could be cut
import { getAudio } from "./helpers/tts.js"
import { aphasiaToText } from "./helpers/transcribe.js";
import { decodeMp3 } from "./helpers/decode.js";
import OpenAI from "openai";
import WebSocket from "ws";
import wav from "wav";

// MAIN RUNNING LOGIC *****************************************************************************************
async function main() {
  // Initialized only once for speed
  const openai = new OpenAI({
        apiKey: process.env.OPENAI_API_KEY,
  });

  // WebSocket Creation
  const url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17";
  const ws = new WebSocket(url, {
    headers: {
      "Authorization": "Bearer " + process.env.OPENAI_API_KEY,
      "OpenAI-Beta": "realtime=v1",
    }
  });

  // WebSocket setting handlers
  ws.on("message", handleEvent);
  ws.on("close", (code, reason) => {console.warn("WS closed:", code, reason?.toString())});
  ws.on("open", function open() {console.log("Connected to server.")});

  // Prompt for Aphasia text is set here eventually by user input
  const prompt = fs.readFileSync("./src/prompts/genericPrompt1.txt").toString()
  console.log(prompt)

  // Output dir is set here eventually by user input
  const outputDir = "output"
  
  // Converts text file into an array of sentences
  const sentences = fs.readFileSync("./src/sentences/set1.txt", "utf8").split("\r\n") // <-- Update to use REGEX and catch/n too
  console.log(sentences);

  await getAudio(sentences, openai, outputDir);
  console.log("Sentences processed!")

  // Get the amount of files in the /output directory
  const files = fs.readdirSync("./output");
  const fileNum = files.length;

  // decodes mp3 data, sends to socket and receives aphasia text
  await decodeMp3(fileNum, ws);

  // Converts aphasia .wavs into sentences and appends to a single file for NLP
  await aphasiaToText(openai);

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

}

// Init 
main();
