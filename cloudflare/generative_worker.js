// Configuration
const CONFIG = {
    DEFAULT_MODEL: '@hf/nousresearch/hermes-2-pro-mistral-7b',
    MODELS: {
        HERMES: '@hf/nousresearch/hermes-2-pro-mistral-7b',
        LLAMA_3: '@cf/meta/llama-3-8b-instruct',
        LLAMA_2: '@cf/meta/llama-2-7b-chat-int8'
    },
    HEADERS: {
        JSON: { 'Content-Type': 'application/json' },
        SSE: { 'Content-Type': 'text/event-stream' }
    }
};

// Input validation utilities
const ValidationUtils = {
    isValidMessages: (messages) => {
        return Array.isArray(messages) &&
            messages.length > 0 &&
            messages.every(msg =>
                typeof msg === 'object' &&
                'content' in msg &&
                'role' in msg
            );
    },

    isValidTools: (tools) => {
        if (!tools) return true;
        return Array.isArray(tools) &&
            tools.every(tool =>
                typeof tool === 'object' &&
                'type' in tool
            );
    }
};

// Response helper functions
const ResponseUtils = {
    error: (message, status = 400) => {
        return new Response(
            JSON.stringify({ error: message }),
            {
                status,
                headers: CONFIG.HEADERS.JSON
            }
        );
    },

    success: (data, isStream = false) => {
        return new Response(
            isStream ? data : JSON.stringify(data),
            {
                headers: isStream ? CONFIG.HEADERS.SSE : CONFIG.HEADERS.JSON
            }
        );
    }
};

// Main request handler
class AIRequestHandler {
    constructor(env) {
        this.env = env;
    }

    async validateRequest(request) {
        if (request.method !== 'POST') {
            throw new Error('Method not allowed. Please use POST.');
        }

        const contentType = request.headers.get('content-type');
        if (!contentType?.includes('application/json')) {
            throw new Error('Content-Type must be application/json');
        }
    }

    async parseRequestBody(request) {
        try {
            const body = await request.json();
            const { messages, stream = false, tools, model } = body;

            if (!ValidationUtils.isValidMessages(messages)) {
                throw new Error('Invalid messages format');
            }

            if (!ValidationUtils.isValidTools(tools)) {
                throw new Error('Invalid tools format');
            }

            return { messages, stream, tools, model };
        } catch (error) {
            throw new Error(`Failed to parse request body: ${error.message}`);
        }
    }

    async processAIRequest({ messages, stream, tools, model }) {
        const selectedModel = model || CONFIG.DEFAULT_MODEL;

        if (!Object.values(CONFIG.MODELS).includes(selectedModel)) {
            throw new Error('Invalid model specified');
        }

        const output = await this.env.AI.run(selectedModel, {
            messages,
            stream: Boolean(stream),
            tools
        });

        return { output, stream };
    }

    async handle(request) {
        try {
            await this.validateRequest(request);
            const requestData = await this.parseRequestBody(request);
            const { output, stream } = await this.processAIRequest(requestData);
            return ResponseUtils.success(output, stream);
        } catch (error) {
            const status = error.message.includes('Method not allowed') ? 405 : 400;
            return ResponseUtils.error(error.message, status);
        }
    }
}

export default {
    async fetch(request, env, ctx) {
        const handler = new AIRequestHandler(env);
        try {
            return await handler.handle(request);
        } catch (error) {
            return ResponseUtils.error('Internal server error', 500);
        }
    }
};