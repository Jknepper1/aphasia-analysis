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

async function main() {
  // Establish interactive terminal element
  const rl = readline.createInterface({input: stdin, output: stdout})
  // initial check
  const normalCheck = fs.readdirSync("normal");
  const aphasiaCheck = fs.readdirSync("aphasia");
  if (normalCheck.length != 0 || aphasiaCheck.length != 0) { 
    const ans = await rl.question("ERROR: Normal audio and/or aphasia directories already contains files... would you like to wipe files and continue? [Y/n]\n")
    if (ans == "Y" || ans == "y") {
      // delete files in output directories
      for (let i = 0; i < normalCheck.length; i++) {
        fs.rmSync(`./normal/${normalCheck[i]}`);
      }
      for (let i = 0; i < aphasiaCheck.length; i++) {
        fs.rmSync(`./aphasia/${aphasiaCheck[i]}`);
      }
    }
    else {
      console.log("Exiting script...")
      process.exit(1);
    }
  }

  let prompt;
  while (true){
    const file = await rl.question("Input the name of your aphasiafier prompt in /src/prompts/: ")
      try {
        prompt = fs.readFileSync(`./src/prompts/${file}`, "utf8");
        console.log(`The full path to the prompt is /src/prompts/${file}`)
        break;
      }
      catch (err){
        console.log(err.message, "try again...");
        continue;
      }
  } 

  let sentences;
  while (true){
    // Converts text file into an array of sentences
    const file = await rl.question("Input a set of sentences from /src/sentences/: ")
      try {
        sentences = fs.readFileSync(`./src/sentences/${file}`, "utf8").split(/\r?\n/) // <-- REGEX to catch \n for non-windows machines
        console.log(`The set of sentences to be aphasiafied is: /src/sentences/${file}`)
        break;
      }
      catch (err){
        console.log(err.message, "try again...");
        continue;
      }
  }

  rl.close();

  // WebSocket Creation - Done early to give time to create - NEEDS TO BE VERIFIED AND LOGGED TO ENSURE CREATION eventually
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
  ws.on("error", (code) => console.log("There has been an error with OpenAI", code) ); // Catch some of the OpenAI error details here to print cleanly and then continue processing if possible



  // Initialized only once for speed
  const openai = new OpenAI({
        apiKey: process.env.OPENAI_API_KEY,
  });

  // Conversion of input text to normal (non-aphasia) audio
  await getAudio(sentences, openai, "normal");
  
  console.log("Sentences converted to normal audio.")
  const normalFiles = fs.readdirSync("normal");

  for (let i = 0; i < normalFiles.length; i++) {
    const fullAudio = await decodeMp3(normalFiles[i]); // Passing in full file name
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
      try  {
        const pcm = Buffer.concat(pcmChunks);
        pcmChunks = [];

        const writer = new wav.FileWriter(
          `./aphasia/processed-${Date.now()}.wav`,
          { channels: 1, sampleRate: 24000, bitDepth: 16 }
        );
        writer.write(pcm);
        writer.end();
      } catch (err) {
        console.log("WAV write failed:", err?.message || err);
      } finally { // Make sure to keep going even if a file failed
        if (continueLoopFn) {
          continueLoopFn(); // Starts as a variable, but is assigned to the resolve function of the Promise instance in the for loop above
          continueLoopFn = null;
        }
      }
    }
  }

  // Converts aphasia .wavs into sentences and appends to a single file for NLP
  console.log("Converting aphasia audio to text...")
  await aphasiaToText(openai);
  console.log("Completed. Script exiting")
  process.exit(0)

}

// Init 
main();
