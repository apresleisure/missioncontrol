const fs = require('fs');
const path = require('path');

// Load central brand state
const statePath = path.join(__dirname, '../config/apres-state.json');
const state = JSON.parse(fs.readFileSync(statePath, 'utf8'));

/**
 * Generates structured creative direction for visual assets
 * @param {string} apparelItem - e.g., "Premium Heavyweight Hoodie"
 * @param {string} environment - e.g., "coastal morning", "downtown transit", "wooded trail"
 */
function generateVisualBrief(apparelItem, environment) {
    const brand = state.brand_rules.name;
    const positioning = state.brand_rules.positioning;

    // Direct enforcement of the terrain-agnostic guardrail
    const prompt = `High-end editorial streetwear photography. A model wearing an unbranded ${apparelItem} in a ${environment} setting. Aesthetic focuses on the "third place"—versatile, premium, and relaxed. Ambient lighting, professional composition. No heavy mountain snow or technical ski gear.`;

    const captionHook = `Designed for the shift. The ${brand} ${apparelItem} transitions seamlessly from early transit to late leisure. Built for ${positioning}. We commit 1% of all proceeds to environmental preservation.`;

    console.log(`\n🎨 CREATIVE BRIEF GENERATED [${apparelItem} - ${environment}]`);
    console.log(`--------------------------------------------------`);
    console.log(`[AI Image Prompt]: ${prompt}`);
    console.log(`[Caption Hook]: ${captionHook}`);

    return { prompt, captionHook };
}

// Example Execution
// generateVisualBrief("Minimalist Shell Jacket", "foggy coastal harbor");

module.exports = { generateVisualBrief };