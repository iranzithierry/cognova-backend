import express from "express";
import axios from "axios";

const app = express();
app.use(express.json());

const PORT = "3000";
const WEBHOOK_VERIFY_TOKEN = "npMCtinGPRFwc523ahbSgEH16MVDLSSc"
const GRAPH_API_TOKEN = "EAAPlrYitZCvIBO556IjDxqYDd7KtyPKhguWUaB4WaoZAhqk1wCIYIJjvZCVtqVAcZB7Pz3P9sSeLJEZAQ1MSKLTduTIZAvtuLQjLF6YfN9EKGFxK3xDGxxHiaOyT5ZAiZBZA6qPndaty3dc52Gh4ZChm46Fqscoj3ZBab3tPf6BH0ZBzrGG1HVzk9OPONVuZBlcOSeZBVH9EAdJjN81bEpCvRCoHZA4UYZBuzXO0kArUrp4cZAu0ZD"

const AI_API_BASE_URL = "https://api.cognova.io/api/v1/bots";

// Dummy data for conversation tracking
const DUMMY_BOT_ID = "d9c3a43b-78ae-4d48-a5e4-44baa8e8253b";
const DUMMY_CONVERSATION_IDS = ["96d2cc0c-0c99-4336-bcfe-aebfddbc4bf8", "48d5af1a-9efb-4479-a479-e7e7173f1d76", "965a8770-b072-4f54-a8ec-791c3c7007b0", "f7c7bf78-0a34-436c-9809-dc7a7fc20ce8"];
const userConversations = new Map();

// Helper function to get or create user conversation
function getOrCreateUserConversation(phoneNumber) {
    console.log("Getting or creating user conversation for", phoneNumber);
    if (!userConversations.has(phoneNumber)) {
        const randomConversationId = DUMMY_CONVERSATION_IDS[
            Math.floor(Math.random() * DUMMY_CONVERSATION_IDS.length)
        ];
        userConversations.set(phoneNumber, randomConversationId);
    }
    return userConversations.get(phoneNumber);
}

// Function to send WhatsApp message
async function sendWhatsAppMessage(phoneNumberId, to, text, replyToMessageId) {
    console.log("Sending message to", to, text);
    const messageData = {
        messaging_product: "whatsapp",
        to,
        text: { body: text },
        ...(replyToMessageId && {
            context: {
                message_id: replyToMessageId,
            },
        }),
    };

    await axios({
        method: "POST",
        url: `https://graph.facebook.com/v18.0/${phoneNumberId}/messages`,
        headers: {
            Authorization: `Bearer ${GRAPH_API_TOKEN}`,
        },
        data: messageData,
    });
}

// Function to mark message as read
async function markMessageAsRead(phoneNumberId, messageId) {
    console.log("Marking message as read", messageId);
    await axios({
        method: "POST",
        url: `https://graph.facebook.com/v18.0/${phoneNumberId}/messages`,
        headers: {
            Authorization: `Bearer ${GRAPH_API_TOKEN}`,
        },
        data: {
            messaging_product: "whatsapp",
            status: "read",
            message_id: messageId,
        },
    });
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

app.post("/webhook", async (req, res) => {
    try {
        const message = req.body.entry?.[0]?.changes[0]?.value?.messages?.[0];
        console.log("Received a message", message)

        if (message?.type === "text") {
            const business_phone_number_id = req.body.entry?.[0].changes?.[0].value?.metadata?.phone_number_id;

            // Mark message as read first
            await markMessageAsRead(business_phone_number_id, message.id);

            // Get or create conversation ID for this user
            const conversationId = getOrCreateUserConversation(message.from);

            // Call AI API
            const aiResponse = await fetch(`${AI_API_BASE_URL}/${DUMMY_BOT_ID}/chat/${conversationId}`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Accept: "text/event-stream",
                },
                body: JSON.stringify({ prompt: message.text.body, }),
            });
    
            const reader = aiResponse.body?.getReader();
            const aiMessageText = await streamChat(reader);

            await sendWhatsAppMessage(
                business_phone_number_id,
                message.from,
                aiMessageText,
                message.id
            );
        }

        res.sendStatus(200);
    } catch (error) {
        console.error('Error processing webhook:', error.message);
        res.sendStatus(500);
    }
});

app.get("/webhook", (req, res) => {
    const mode = req.query["hub.mode"];
    const token = req.query["hub.verify_token"];
    const challenge = req.query["hub.challenge"];

    if (mode === "subscribe" && token === WEBHOOK_VERIFY_TOKEN) {
        res.status(200).send(challenge);
        console.log("Webhook verified successfully!");
    } else {
        res.sendStatus(403);
    }
});

app.get("/", (req, res) => {
    res.send(`<pre>Hello, World</pre>`);
});

app.listen(PORT, () => {
    console.log(`Server is listening on port: ${PORT}`);
});
// pm2 start node -- app.js