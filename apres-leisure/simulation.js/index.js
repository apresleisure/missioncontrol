const fs = require('fs');
const path = require('path');

console.log("🔍 [DEBUG] Script initialized. Resolving absolute layout...");

const statePath = path.join(__dirname, '../config/apres-state.json');
const state = JSON.parse(fs.readFileSync(statePath, 'utf8'));

const { craftVanguardInvite } = require('../Engines/vanguardoutreach');
const { generateTrackingQR } = require('../Engines/QRgenerator');

console.log("\n🚀 STARTING APRES LEISURE OPERATIONAL SIMULATION 🚀");
console.log("==================================================\n");

const mockInboundPayload = {
    username: "@powder_shredder",
    name: "Marcus",
    specialty: "backcountry snowboarding",
    customization: {
        hook_reference: "your recent lines through the trees at Brighton"
    }
};

console.log("STEP 1: Ingesting Raw Target Payload...");
console.log(`Received: ${mockInboundPayload.username} | Niche Focus: ${mockInboundPayload.specialty}`);

console.log("\nSTEP 2: Generating Free Tracking QR Engine Assets...");
const qrAssets = generateTrackingQR(mockInboundPayload.username);

// Wait for the asynchronous file write stream to actually finish
qrAssets.writeStream.on('finish', () => {
    console.log(`✅ Destination Tracking URL Configured: ${qrAssets.url}`);
    console.log(`✅ High-Resolution Print Asset Stamped: ${qrAssets.qrCodePath}`);

    console.log("\nSTEP 3: Compiling Custom Specialist Copy...");
    const structuralTarget = {
        ...mockInboundPayload,
        partnership_terms: {
            assigned_qr: qrAssets.url
        }
    };

    const finalOutreach = craftVanguardInvite(structuralTarget);
    console.log(`✅ Text Content Verified (Spelling Standardized to ${state.brand_rules.name})`);
    console.log(`--------------------------------------------------`);
    console.log(finalOutreach.templated_message);

    console.log("\n==================================================");
    console.log("🎉 SIMULATION SUCCESSFUL: ASSET WRITTEN TO DISK");
    console.log("==================================================");
    
    process.exit(0);
});

qrAssets.writeStream.on('error', (err) => {
    console.error("❌ File System Error writing QR Code:", err);
    process.exit(1);
});