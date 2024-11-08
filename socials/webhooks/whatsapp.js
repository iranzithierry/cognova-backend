import express from "express";
import axios from "axios";

const app = express();
app.use(express.json());

const PORT = "3000"
const WEBHOOK_VERIFY_TOKEN = "npMCtinGPRFwc523ahbSgEH16MVDLSSc"
const GRAPH_API_TOKEN = "EAAPlrYitZCvIBOwQZByZCOtgiMRm3BJhUXmsPBgaIWpY2ZBioQHozGVWGnfGo7OeOFoEkcQ2fqtyZB7LoSHK3or7YBnkmYKmiEylBbJhptroekaXMnYZCCpcRSAIb5ZC2qaSgZAEGSkyDnTZC5eZB0SPbYLWZCZAZBgbSONZBM4RpZCDHurcIVr2fA3XWxV346SdcwT9ZAzAj7bdikapTmkwXALKyScuLSAbSbiU"

app.post("/webhook", async (req, res) => {
    const message = req.body.entry?.[0]?.changes[0]?.value?.messages?.[0];

    if (message?.type === "text") {
        const business_phone_number_id = req.body.entry?.[0].changes?.[0].value?.metadata?.phone_number_id;
        await axios({
            method: "POST",
            url: `https://graph.facebook.com/v18.0/${business_phone_number_id}/messages`,
            headers: {
                Authorization: `Bearer ${GRAPH_API_TOKEN}`,
            },
            data: {
                messaging_product: "whatsapp",
                to: message.from,
                text: { body: "Echo: " + message.text.body },
                context: {
                    message_id: message.id, // shows the message as a reply to the original user message
                },
            },
        });

        await axios({
            method: "POST",
            url: `https://graph.facebook.com/v18.0/${business_phone_number_id}/messages`,
            headers: {
                Authorization: `Bearer ${GRAPH_API_TOKEN}`,
            },
            data: {
                messaging_product: "whatsapp",
                status: "read",
                message_id: message.id,
            },
        });
    }

    res.sendStatus(200);
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
