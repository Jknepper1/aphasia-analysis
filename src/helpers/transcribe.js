import fs from "fs";

// Takes aphasia audio and converts to text
export async function aphasiaToText(openai) {
  const files = fs.readdirSync("./aphasia");
  let i = 0;
  for (const file of files) {
    const transcription = await openai.audio.transcriptions.create({
    file: fs.createReadStream("./aphasia/" + file),
    model: "gpt-4o-transcribe"
    })

    // console.log(transcription.text);
    
    // Prevents the file from being rewritten each subsequent sentence after the first
    if (i >= 1) {
      fs.appendFileSync("./src/aphasiaText/scriptResults.txt", transcription.text + "\n")
    } else {
      fs.writeFileSync("./src/aphasiaText/scriptResults.txt", transcription.text + "\n")
    }
    // TODO: Implement a method for inserting ellipsis if there is a long enough pause in the audio
    // TODO: Don't have the script write to the same file each time, so that multiple runs can be stored
    // TODO: Have these runs named in a way that relates to the prompt and sentences used in the run
    i++;
  }
};