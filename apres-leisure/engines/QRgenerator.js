const express = require('express');
const path = require('path');
const fs = require('fs');

// 1. Import your newly verified core engines
const { generateTrackingQR } = require('./Engines/QRgenerator');
const { craftVanguardInvite } = require('./Engines/vanguardoutreach');

const app = express();
app.use(express.json()); // Essential to parse incoming webhook payloads

// Load your terrain-agnostic state rules to verify global parameters
const statePath = path.join(__dirname, './config/apres-state.json');
const state = JSON.parse(fs.readFileSync(statePath, 'utf8'));

/**
 * @route   POST /api/v1/vanguard-webhook
 * @desc    Catches incoming Make.com payloads, stamps unique tracking vectors, 
 *          and compiles targeted lifestyle activation outreach copy.
 */
app.post('/api/v1/vanguard-webhook', (req, res) => {
    try {
        const { username, name, specialty, hook_reference } = req.body;

        // Fail early if the webhook payload lacks critical routing variables
        if (!username || !name) {
            return res.status(400).json({
                success: false,
                error: "Missing required parameters: 'username' and 'name' must be provided."
            });
        }

        console.log(`\n⚡ [WEBHOOK] Processing Inbound Specialist: ${username}`);

        // Step 1: Initialize the tracking asset generation via the QR Engine
        const qrAssets = generateTrackingQR(username);

        // Step 2: Wait for the vector stream to lock into your local repository
        qrAssets.writeStream.on('finish', () => {
            console.log(`✅ Asset written to disk: ${qrAssets.fileName}`);

            // Step 3: Bundle the payload properties for the outreach compiler
            const structuralTarget = {
                username,
                name,
                specialty: specialty || "all-terrain operator",
                partnership_terms: {
                    assigned_qr: qrAssets.url
                }
            };

            // Step 4: Run it through the standardized spelling engine
            const compiledOutreach = craftVanguardInvite(structuralTarget);

            // Step 5: Deliver the clean payload straight back to Make.com / Klaviyo
            return res.status(200).json({
                success: true,
                meta: {
                    brand: state.brand_rules.name,
                    tracking_node: qrAssets.url,
                    local_asset_path: qrAssets.qrCodePath
                },
                outreach: {
                    recipient: compiledOutreach.recipient,
                    message: compiledOutreach.templated_message
                }
            });
        });

        // Error boundary specifically for file system write blocks
        qrAssets.writeStream.on('error', (streamErr) => {
            console.error("❌ File System Stream Error:", streamErr);
            return res.status(500).json({
                success: false,
                error: "Failed to write vector QR asset to server file system."
            });
        });

    } catch (globalErr) {
        console.error("❌ Critical Integration Error:", globalErr);
        return res.status(500).json({
            success: false,
            error: "Internal configuration error processing vanguard routing plumbing."
        });
    }
});

// Start your service layer
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`\n==================================================`);
    console.log(`🚀 APRES LEISURE AUTOMATION CORE RUNNING ON PORT ${PORT}`);
    console.log(`==================================================`);
});

const qr = require('qr-image');
const fs = require('fs');
const path = require('path');

/**
 * Generates a free vector SVG QR code for tracking a specialist's network activity
 * Passes back the active write stream reference to prevent premature process termination
 * @param {string} username - The social handle of the inbound Vanguard specialist
 * @returns {Object} Tracking data metadata, output path, and the active writeStream instance
 */
function generateTrackingQR(username) {
    // Standardize handle formatting for clean path management
    const cleanUsername = username.replace('@', '').toLowerCase();
    
    // Configured tracking URL mapped to your redeveloped domain
    const trackingUrl = `url?id=12/${cleanUsername}`; 
    
    // Generate clean vector stream for high-resolution print pack-ins
    const qrSvg = qr.image(trackingUrl, { type: 'svg', size: 10 });
    
    // Step outside the Engines directory to standard pathing: ../data/qrs
    const outputDir = path.join(__dirname, '../data/qrs');
    
    // Gracefully handle directory initialization if it doesn't exist yet
    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
    }
    
    const fileName = `qr_${cleanUsername}.svg`;
    const outputPath = path.join(outputDir, fileName);
    
    // Capture the write stream instance so the caller can handle async lifecycle hooks
    const writeStream = fs.createWriteStream(outputPath);
    qrSvg.pipe(writeStream);
    
    return {
        url: trackingUrl,
        qrCodePath: outputPath,
        fileName: fileName,
        writeStream: writeStream // Critical handoff for async orchestration
    };
}

// Lock this object export format in so the destructuring assignment works cleanly
module.exports = { generateTrackingQR };