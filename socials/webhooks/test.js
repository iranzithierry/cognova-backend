import express from "express";
import axios from "axios";

const app = express();
app.use(express.json());

const PORT = "3000";

const AI_API_BASE_URL = "https://api.cognova.io/api/v1/bots";

// Function to process AI response stream
const streamChat = async (reader) => {
    let fullContent = "";
    const decoder = new TextDecoder();
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split("\n");
        for (const line of lines) {
            if (line.startsWith("data: ")) {
                const data = JSON.parse(line.slice(5));
                if ("token" in data) {
                    fullContent += data.token;
                }
            }
        }
    }
    return fullContent;
};


app.post("/webhook", async (req, res) => {
    try {
        const response = await fetch(`${AI_API_BASE_URL}/d9c3a43b-78ae-4d48-a5e4-44baa8e8253b/chat/96d2cc0c-0c99-4336-bcfe-aebfddbc4bf8`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Accept: "text/event-stream",
            },
            body: JSON.stringify({ prompt: "hi", }),
        });

        const reader = response.body?.getReader();
        // Process the stream and get complete response
        const aiMessageText = await streamChat(reader);
        console.log("AI 2", aiMessageText)
        res.sendStatus(200);
    } catch (error) {
        console.error('Error processing webhook:', error.message);
        res.sendStatus(500);
    }
});

app.listen(PORT, () => {
    console.log(`Server is listening on port: ${PORT}`);
});