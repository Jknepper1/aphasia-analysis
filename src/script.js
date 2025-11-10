import "dotenv/config";
import fs from "fs"; // Could be cut
import { getAudio } from "./helpers/tts.js"
import { aphasiaToText } from "./helpers/transcribe.js";
import { decodeMp3 } from "./helpers/decode.js";
import OpenAI from "openai";
import WebSocket from "ws";
import wav from "wav";
import * as readline from 'node:readline/promises';
import { stdin, stdout } from "node:process";

let pcmChunks = [];
let continueLoopFn;


// MAIN RUNNING LOGIC *****************************************************************************************
async function main() {
  // Establish interactive terminal element
  const rl = readline.createInterface({input: stdin, output: stdout})
  let outputDir;
  let prompt;
  let sentences;

  while (true){
    const file = await rl.question("Input the name of your aphasiafier prompt in /src/prompts/: ")
    console.log(`The full path to the prompt is /src/prompts/${file}`)
      try {
        prompt = fs.readFileSync(`./src/prompts/${file}`, "utf8");
        break;
      }
      catch (err){
        console.log(`ERROR: ${file} does not exist... try again \n`);
        continue;
      }
  } 

  while (true){
    // Output dir is set here eventually by user input
    const dir = await rl.question("Input your desired output directory in /aphasia-analysis/: ")
    console.log(`The name of your output directory is: /aphasia-analysis/${dir}`)
      try {
        outputDir = fs.readdirSync(dir);
        break;
      }
      catch (err){
        console.log(`ERROR: ${dir} does not exist... try again \n`);
        continue;
      }
  }

  while (true){
    // Converts text file into an array of sentences
    const file = await rl.question("Input a set of sentences from /src/sentences/: ")
    console.log(`The set of sentences to be aphasiafied is: /src/sentences/${file}`)
      try {
        sentences = fs.readFileSync(`./src/sentences/${file}`, "utf8").split(/\r?\n/) // <-- REGEX to catch \n for non-windows machines
        break;
      }
      catch (err){
        console.log(`ERROR: ${file} does not exist... try again \n`);
        continue;
      }
  }

  rl.close();


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
  ws.on("open", function open() {console.log("Connected to WebSocket server.")});

  await getAudio(sentences, openai, outputDir);
  console.log("Sentences converted to normal audio.")

  for (let i = 0; i < outputDir.length; i++) {
    const fullAudio = await decodeMp3(outputDir[i]); // Passing in full file name
    // decodes mp3 data, sends to socket and receives aphasia text
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
    ws.send(JSON.stringify(event));
    ws.send(JSON.stringify({ type: "response.create"})) // This should trigger the building of a response object based upon the last message sent
    await new Promise((resolve) => {continueLoopFn = resolve}) // Maintains consistent pacing with API messages by awaiting response.audio.done handler 
    // continueLoopFn = resolve just makes the resolve function globally accessible so the handleEvent function can see it and execute it. It's like pausing the Promise and then handing the remote to the HandleEvent function
  }


  // Converts aphasia .wavs into sentences and appends to a single file for NLP
  await aphasiaToText(openai);

  
  function handleEvent(data) {
    const serverEvent = JSON.parse(data);

    if (serverEvent.type === "session.created") {
      console.log("API session created.");
      ws.send(JSON.stringify({
        type: "session.update",
        session: {
          instructions: prompt // Prompt set by variable at top of file
        }
      }));
    }

    if (serverEvent.type === "session.updated") {
      console.log("Prompt set in API session.")
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
      writer.end(); // () => console.log("processed-XX.wav written")
      
      if (continueLoopFn) {
        continueLoopFn(); // Starts as a variable, but is assigned to the resolve function of the Promise instance in the for loop above
        continueLoopFn = null;
      }
    }
  }
}

// Init 
main();
