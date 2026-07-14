const fs = require('fs');
const path = require('path');

const statePath = path.join(__dirname, '../config/apres-state.json');
const state = JSON.parse(fs.readFileSync(statePath, 'utf8'));

/**
 * Drafts custom outreach targeting niche specialists with early-stage transparency
 * @param {object} target - The screened creator object from vanguard-targets.json
 */
function craftSpecialistInvite(target) {
    const brand = state.brand_rules.name; // Resolves cleanly to "Apres"

    const message = `Hey ${target.name}, saw ${target.customization.hook_reference}—your content in ${target.specialty} is exactly the energy we love. We're launching ${brand} Leisure. We are just starting out, hitting the ground running, and looking to build genuine relationships with creators who are elite at what they do. We don't have corporate red tape—we're just a lean team focused on making premium gear for the downtime after the session. Want us to drop a vanguard kit to your coordinates and sync up on a unique tracking QR for your crew? Let us know if you're down to build with us.`;

    return {
        username: target.username,
        qr_code: target.partnership_terms.assigned_qr,
        templated_message: message
    };
}

module.exports = { craftSpecialistInvite };