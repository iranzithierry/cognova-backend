import express from "express";
import axios from "axios";

const app = express();
app.use(express.json());

const PORT = "3098";
const VERIFY_TOKEN = "npMCtinGPRFwc523ahbSgEH16MVDLSSc"
const INSTAGRAM_ACCESS_TOKEN = "your_instagram_access_token_here";

const AI_API_BASE_URL = "https://api.cognova.io/api/v1/bots";
const DUMMY_BOT_ID = "d9c3a43b-78ae-4d48-a5e4-44baa8e8253b";
const DUMMY_CONVERSATION_IDS = ["96d2cc0c-0c99-4336-bcfe-aebfddbc4bf8", "48d5af1a-9efb-4479-a479-e7e7173f1d76"];
const userConversations = new Map();

// Helper function to get or create user conversation
function getOrCreateUserConversation(userId) {
    if (!userConversations.has(userId)) {
        const randomConversationId = DUMMY_CONVERSATION_IDS[
            Math.floor(Math.random() * DUMMY_CONVERSATION_IDS.length)
        ];
        userConversations.set(userId, randomConversationId);
    }
    return userConversations.get(userId);
}

// Function to send Instagram DM
async function sendInstagramMessage(userId, message) {
    try {
        await axios({
            method: "POST",
            url: `https://graph.facebook.com/v18.0/me/messages`,
            headers: {
                Authorization: `Bearer ${INSTAGRAM_ACCESS_TOKEN}`,
            },
            data: {
                recipient: {
                    id: userId,
                },
                message: {
                    text: message,
                },
                messaging_type: "RESPONSE",
            },
        });
        console.log("Message sent successfully to", userId);
    } catch (error) {
        console.error("Error sending message:", error.message);
        throw error;
    }
}

// Function to mark message as read
async function markMessageAsRead(userId) {
    try {
        await axios({
            method: "POST",
            url: `https://graph.facebook.com/v18.0/me/messages`,
            headers: {
                Authorization: `Bearer ${INSTAGRAM_ACCESS_TOKEN}`,
            },
            data: {
                recipient: {
                    id: userId,
                },
                sender_action: "mark_seen",
            },
        });
        console.log("Marked messages as read for", userId);
    } catch (error) {
        console.error("Error marking message as read:", error.message);
        throw error;
    }
}

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

// Webhook endpoint for Instagram
app.post("/webhook", async (req, res) => {
    try {
        // Get the message event
        const entry = req.body.entry?.[0];
        const messaging = entry?.messaging?.[0];

        if (!messaging || !messaging.message) {
            return res.sendStatus(200);
        }

        const senderId = messaging.sender.id;
        const messageText = messaging.message.text;

        // Mark the message as read
        await markMessageAsRead(senderId);

        // Get or create conversation ID for this user
        const conversationId = getOrCreateUserConversation(senderId);

        // Call AI API for response
        const aiResponse = await fetch(`${AI_API_BASE_URL}/${DUMMY_BOT_ID}/chat/${conversationId}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Accept: "text/event-stream",
            },
            body: JSON.stringify({
                prompt: messageText,
            }),
        });

        const reader = aiResponse.body?.getReader();
        const aiMessageText = await streamChat(reader);

        // Send the response back to Instagram
        await sendInstagramMessage(senderId, aiMessageText);

        res.sendStatus(200);
    } catch (error) {
        console.error("Error processing webhook:", error.message);
        res.sendStatus(500);
    }
});

// Webhook verification endpoint
app.get("/webhook", (req, res) => {
    const mode = req.query["hub.mode"];
    const token = req.query["hub.verify_token"];
    const challenge = req.query["hub.challenge"];

    if (mode === "subscribe" && token === VERIFY_TOKEN) {
        console.log("Webhook verified successfully!");
        res.status(200).send(challenge);
    } else {
        res.sendStatus(403);
    }
});

// Health check endpoint
app.get("/", (req, res) => {
    res.send(`<pre>Instagram Bot Server Running</pre>`);
});

app.listen(PORT, () => {
    console.log(`Server is listening on port: ${PORT}`);
});