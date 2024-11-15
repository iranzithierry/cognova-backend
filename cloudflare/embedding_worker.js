const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Accept-Encoding',
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

        const formattedData = response.data.map((embedding, index) => ({
            object: "embedding",
            embedding,
            index
        }));
        return {
            object: "list",
            data: formattedData,
            model,
            usage: {
                prompt_tokens: input.length,
                total_tokens: input.length
            }
        };
    } catch (error) {
        return {
            success: false,
            error: error.message,
        };
    }
}

async function compressResponse(jsonResponse) {
    const encoder = new TextEncoder();
    const bytes = encoder.encode(JSON.stringify(jsonResponse));
    const cs = new CompressionStream('gzip');
    const writer = cs.writable.getWriter();
    writer.write(bytes);
    writer.close();
    return new Response(cs.readable).arrayBuffer();
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

        // Check if client accepts gzip encoding
        const acceptEncoding = request.headers.get('accept-encoding') || '';
        const supportsGzip = acceptEncoding.includes('gzip');

        if (supportsGzip) {
            const compressed = await compressResponse(result);
            return new Response(compressed, {
                headers: {
                    'Content-Type': 'application/json',
                    'Content-Encoding': 'gzip',
                    'Vary': 'Accept-Encoding',
                    ...corsHeaders,
                },
            });
        } else {
            return new Response(JSON.stringify(result), {
                headers: {
                    'Content-Type': 'application/json',
                    ...corsHeaders,
                },
            });
        }

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