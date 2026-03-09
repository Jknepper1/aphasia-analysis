import "dotenv/config";
import fs from "fs";
import path from "path";  
import { getAudio } from "./helpers/tts.js"
import { aphasiaToText } from "./helpers/transcribe.js";
import { decodeMp3, writeWav } from "./helpers/decode.js";
import OpenAI from "openai";
import WebSocket from "ws";
import * as readline from 'node:readline/promises';
import { stdin, stdout } from "node:process";

async function setup() {
  // Establish interactive terminal element
  const rl = readline.createInterface({input: stdin, output: stdout})
  
  // initial check
  if (!fs.existsSync("normal")) fs.mkdirSync("normal");
  if (!fs.existsSync("aphasia")) fs.mkdirSync("aphasia");

  const normalCheck = fs.readdirSync("normal");
  const aphasiaCheck = fs.readdirSync("aphasia");

  // Now it is safe to read them
  if (normalCheck.length != 0 || aphasiaCheck.length != 0) { 
    const ans = await rl.question("ERROR: Normal audio and/or aphasia directories already contains files... would you like to wipe files? [Y/n]\n")
    if (ans == "Y" || ans == "y") {
      // delete files in output directories
      for (let i = 0; i < normalCheck.length; i++) {
        fs.rmSync(`./normal/${normalCheck[i]}`);
      }
      for (let i = 0; i < aphasiaCheck.length; i++) {
        fs.rmSync(`./aphasia/${aphasiaCheck[i]}`);
      }
    }
  }

  const point = await rl.question("Where would you like to start? [0: Beginning, 1: NormalToAphasia, 2: Transcription]\n")
  
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

  const normalDir = await rl.question("Input the name of your normal audio directory in /normal/: ")
  const aphasiaDir = await rl.question("Input the name of your aphasia audio directory in /aphasia/: ")

  rl.close();
  
  return { point, prompt, sentences, normalDir, aphasiaDir }; // 0 means start at beginning, 1 means start at normal to aphasia, 2 means start at transcription. Set by user input in main()
}



async function main() {
  let currentResolve = null;
  let currentChunks = [];

  // Get all vars from setup() and then destructure for use
  let { point, prompt, sentences, normalDir, aphasiaDir } = await setup();
  

  // WebSocket Creation - Done early to give time to create - NEEDS TO BE VERIFIED AND LOGGED TO ENSURE CREATION eventually
  // POTENTIALLY UPDATE TO NEWER MODEL, Should be roughly 20% more cost effective 
  const url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17";
  const ws = new WebSocket(url, {
    headers: {
      "Authorization": "Bearer " + process.env.OPENAI_API_KEY,
      "OpenAI-Beta": "realtime=v1", // This has to be removed for the newer model
    }
  });
  // Initialized only once for speed
  const openai = new OpenAI({
        apiKey: process.env.OPENAI_API_KEY,
  });

  if (point == "0") { 
  // Skipped if the user selects start at NormalToAphasia or transcription
  
  // Conversion of input text to normal (non-aphasia) audio
  await getAudio(sentences, openai, normalDir);
  
  console.log("Sentences converted to normal audio.")
  // Decodes normal audio, sends to socket, receives aphasia audio, writes aphasia audio to file, converts aphasia audio to text
  }

  if (point == "1" || point == "0") {
    // WebSocket setting handlers
    ws.on("message", handleEvent);
    ws.on("close", (code, reason) => {console.warn("WS closed:", code, reason?.toString())});
    ws.on("error", (code) => console.log("There has been an error with OpenAI", code) ); // Catch some of the OpenAI error details here to print cleanly and then continue processing if possible

    // Ensures the WebSocket is open before continuing the script
    await new Promise((resolve) => {
      ws.on("open", () => {
        console.log("Connected to WebSocket server.");
        resolve(); 
      });
    });

    const normalFiles = fs.readdirSync("normal");
    for (let i = 0; i < normalFiles.length; i++) {
      const fullAudio = await decodeMp3(normalFiles[i]);

      console.log(`sentence ${i}`);

      const waitPromise = new Promise((resolve) => {
        currentResolve = resolve;
      });

      ws.send(JSON.stringify({
        type: "conversation.item.create",
        item: {
          type: "message",
          role: "user",
          content: [{ type: "input_audio", audio: fullAudio }]
        }
      }));

      ws.send(JSON.stringify({ type: "response.create" }));

      await waitPromise;
    }

    function handleEvent(data) {
      const serverEvent = JSON.parse(data);

      if (serverEvent.type === "session.created") {
        console.log("API session created.");
        ws.send(JSON.stringify({
          type: "session.update",
          session: {
            instructions: prompt // Prompt set by variable by global var
          }
        }));
        
      }

      if (serverEvent.type === "session.updated") {
        console.log("Prompt set in API session.")
      }

      if (serverEvent.type === "response.audio.delta") {
        // Access Base64-encoded audio chunks
        currentChunks.push(Buffer.from(serverEvent.delta, "base64"))
      }

      if (serverEvent.type === "response.audio.done") {
        const pcm = Buffer.concat(currentChunks);
        currentChunks = [];


        const aphasiaDir = path.resolve("./aphasia");
        fs.mkdirSync(aphasiaDir, { recursive: true });
        const filePath = path.join(aphasiaDir,  `/processed-${Date.now()}.wav`)
        console.log("Does aphasia exist:", fs.existsSync(aphasiaDir));
        
        writeWav(filePath, pcm);
        
        if (currentResolve) {
          currentResolve();
          currentResolve = null;
        }
      }
    }
  }

  // Converts aphasia .wavs into sentences and appends to a single file for NLP
  console.log("Converting aphasia audio to text...")
  await aphasiaToText(openai, aphasiaDir);
  console.log("Completed. Script exiting")
  process.exit();
}

// Init 
main();
