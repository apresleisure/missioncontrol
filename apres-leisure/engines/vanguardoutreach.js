const fs = require('fs');
const path = require('path');

/**
 * Crafts a personalized network invitation for an inbound vanguard operator
 * Standardizes spelling constraints based on global brand state configuration
 * @param {Object} target - The structured specialist payload data
 * @returns {Object} Final rendered email message template copy
 */
function craftVanguardInvite(target) {
    const statePath = path.join(__dirname, '../config/apres-state.json');
    const state = JSON.parse(fs.readFileSync(statePath, 'utf8'));
    
    // Dynamically respect the terrain-agnostic branding rules
    const brandName = state.brand_rules.name;

    const templated_message = `
// VANGUARD INBOUND DETECTED //
--------------------------------------------------
Hey ${target.name},

Saw your recent lines through the trees at Brighton. Absolute class. 

At ${brandName} Leisure, we're building a network for operators who live in the transition—from the trailhead to the transit hub, perimeter to apres. 

We've provisioned a custom tracking node for your network activity. Scan the asset below to initialize your profile and log your first Lore Points on the network ledger.

Your Activation QR Link: ${target.partnership_terms.assigned_qr}

Welcome to the vanguard.
--------------------------------------------------
    `.trim();

    return {
        recipient: target.username,
        templated_message: templated_message
    };
}

module.exports = { craftVanguardInvite };
