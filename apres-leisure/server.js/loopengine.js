const express = require('express');
const axios = require('axios');
const fs = require('fs');
const app = express();
app.use(express.json());

// Load the external memory
const state = JSON.parse(fs.readFileSync('./apres-state.json', 'utf8'));

app.post('/api/generate-copy', async (req, res) => {
    const { taskType, audienceData } = req.body;

    const systemPrompt = `
        You are the Apres Leisure Growth Architect.
        Brand Name: ${state.brand_rules.name} (Never use an accent).
        Positioning: ${state.brand_rules.positioning}. If you mention mountains, you must balance it with city streets or coastal environments.
        Mandate: Always weave in our ${state.brand_rules.commitments[0]} organically.
        Task: Apply Halbert direct-response principles to draft a ${taskType}.
    `;

    try {
        // Call your preferred LLM API here (Claude/OpenAI) using the systemPrompt
        const aiResponse = await callLLM(systemPrompt, audienceData); 
        
        // Format the output specifically for Make.com to push downstream
        res.json({
            status: "success",
            copy: aiResponse,
            // Ensure data routing is clean for downstream Klaviyo updates
            klaviyo_endpoint: "/api/profiles/" 
        });

    } catch (error) {
        console.error("Loop Engine Error:", error);
        res.status(500).send("Agent failed to generate copy.");
    }
});

app.listen(3000, () => console.log('Apres Loop Engine running on port 3000'));