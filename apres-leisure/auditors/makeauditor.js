const fs = require('fs');

// Configuration for Make.com Free Tier Guardrails
const FREE_TIER_LIMITS = {
    maxModules: 5,            // Keeping scenarios lean to manage complexity
    bannedDataStructures: [
        "/api/api/",         // Flag duplicated path errors
        "//profiles"
    ]
};

function auditScenario(blueprintPath) {
    try {
        const fileContent = fs.readFileSync(blueprintPath, 'utf8');
        const blueprint = JSON.parse(fileContent);
        
        const modules = blueprint.flow || [];
        const errors = [];
        const warnings = [];

        console.log(`\n🔍 Auditing Make Scenario: ${blueprint.name || 'Unnamed Scenario'}`);
        console.log(`--------------------------------------------------`);

        // 1. Structural Free Tier Check
        if (modules.length > FREE_TIER_LIMITS.maxModules) {
            warnings.push(`[Free Tier Risk] Scenario uses ${modules.length} modules. To optimize operational efficiency and minimize execution failures, split complex flows into decoupled webhook-centric scenarios.`);
        }

        // 2. Loop & Endpoint Integrity Check
        const blueprintString = JSON.stringify(blueprint);
        FREE_TIER_LIMITS.bannedDataStructures.forEach(pattern => {
            if (blueprintString.includes(pattern)) {
                errors.push(`[Critical Integration Error] Found malformed URL/API path pattern: "${pattern}". Verify endpoint parameters (e.g., ensure Klaviyo paths resolve strictly to /api/profiles/).`);
            }
        });

        // 3. Interval & Trigger Check (Heartbeat Optimization)
        modules.forEach(mod => {
            if (mod.metadata && mod.metadata.type === 'trigger' && mod.parameters?.interval < 15) {
                warnings.push(`[Efficiency Warning] Module ${mod.title || mod.id} runs at high frequency. For terrain-agnostic background loops, transition to instant Webhooks instead of constant polling to conserve operation counts.`);
            }
        });

        // Output Results
        if (errors.length === 0 && warnings.length === 0) {
            console.log("✅ Scenario is clean, optimized, and ready for deployment.");
        } else {
            errors.forEach(err => console.log(`❌ ERROR: ${err}`));
            warnings.forEach(warn => console.log(`⚠️ WARNING: ${warn}`));
        }

    } catch (error) {
        console.error("❌ Failed to parse scenario blueprint:", error.message);
    }
}

// Example usage: Point this to your exported Make blueprint
// auditScenario('./blueprints/klaviyo-loop-blueprint.json');

module.exports = { auditScenario };