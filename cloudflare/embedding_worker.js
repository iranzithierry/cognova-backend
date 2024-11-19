const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
};

async function handleOptions(request) {
    return new Response(null, {
        headers: corsHeaders,
    });
}

async function generateEmbeddings(env, input, model = "@cf/baai/bge-large-en-v1.5") {
    try {
        const isArray = Array.isArray(input);
        const textInput = isArray ? { text: input } : { text: [input] };

        const response = await env.AI.run(model, textInput);

        const formattedData = [];
        for (var i = 0; i < response.data.length; i++) {
            formattedData.push({
                embedding: response.data[i],
                index: i,
                object: "embedding"
            })
        }
        return {

            data: formattedData,
        };
    } catch (error) {
        return {
            success: false,
            error: error.message,
        };
    }
}

async function handleRequest(request, env) {
    if (request.method !== 'POST') {
        return new Response(JSON.stringify({
            success: false,
            error: 'Only POST method is allowed'
        }), {
            status: 405,
            headers: {
                'Content-Type': 'application/json',
                ...corsHeaders,
            },
        });
    }

    try {
        const allowedModels = [
            "@cf/baai/bge-large-en-v1.5",
            "@cf/baai/bge-base-en-v1.5",
            "@cf/baai/bge-small-en-v1.5",
        ]
        const contentType = request.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            throw new Error('Content-Type must be application/json');
        }

        const body = await request.json();
        if (!body.input) {
            throw new Error('Request must include a "input" field');
        }
        let model = "@cf/baai/bge-large-en-v1.5"
        if (body.model && allowedModels.includes(body.model)) {
            model = body.model
        }
        const result = await generateEmbeddings(env, body.input, model);

        return new Response(JSON.stringify(result), {
            headers: {
                'Content-Type': 'application/json',
                ...corsHeaders,
            },
        });

    } catch (error) {
        return new Response(JSON.stringify({
            success: false,
            error: error.message,
        }), {
            status: 400,
            headers: {
                'Content-Type': 'application/json',
                ...corsHeaders,
            },
        });
    }
}

export default {
    async fetch(request, env) {
        if (request.method === 'OPTIONS') {
            return handleOptions(request);
        }

        return handleRequest(request, env);
    },
};