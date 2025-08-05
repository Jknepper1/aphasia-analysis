import path from "path";
import fs from "fs/promises"; //fs/promises?

// Get the amount of files in the /output directory
const output = path.resolve(`./output`);
const files= await fs.readdir(output);
const fileNum = files.length;
console.log(fileNum);


export async function convertAudioToTranscript() {
    for (let i = 0; i < fileNum; i++) {
        const file = path.resolve(`./output/speech${i}.mp3`)
        const data = await fs.readFile(file, null)

        const form = new FormData();
        form.append("tabNum", 1);
        form.append("voice", "Coral")
        form.append("audio", new Blob([data], { type: "audio/mp3" }), `speech${i}.mp3`);
        
        console.log(file);
        const url = "http://localhost:5173/api/analysis" // CHANGE TO PROD WHEN TIME COMES
        
        try {
            const response = await fetch(url, {
                method: "POST",
                headers: {
                    "Content-Type": "audio/mp3"
                },
                body: data // Buffered audio data and instructions
            })
            if(response.ok) {
                console.log("Got an ok!")
            }
            else {
                console.log(response.statusText)
            }
        } catch (err) {
            console.error("Error sending audio file: ", err)
        } 
    }
}