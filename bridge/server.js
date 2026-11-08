/**
 * server.js - WhatsApp Local Bridge Microservice using Baileys.
 * Runs on 127.0.0.1:5001. Provides HTTP endpoints for Python desktop app:
 * - GET  /status   : Check connection status and get QR code
 * - POST /send-bill: Send automated bill message and/or PDF invoice
 * - POST /logout   : Disconnect current session
 */

const express = require('express');
const { default: makeWASocket, useMultiFileAuthState, DisconnectReason } = require('@whiskeysockets/baileys');
const pino = require('pino');
const QRCode = require('qrcode');
const fs = require('fs');
const path = require('path');

const app = express();
app.use(express.json());

const PORT = 5001;
const AUTH_DIR = path.join(__dirname, 'auth_info');

let sock = null;
let connectionStatus = 'connecting';
let qrDataUrl = null;
let userInfo = null;
let lastError = null;

async function connectToWhatsApp() {
    connectionStatus = 'connecting';
    lastError = null;

    try {
        const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);

        sock = makeWASocket({
            logger: pino({ level: 'silent' }),
            printQRInTerminal: false,
            auth: state,
            browser: ['Soni Natvarlal Himmatlal', 'Chrome', '1.0.0']
        });

        sock.ev.on('connection.update', async (update) => {
            const { connection, lastDisconnect, qr } = update;

            if (qr) {
                try {
                    qrDataUrl = await QRCode.toDataURL(qr, {
                        margin: 4,
                        width: 360,
                        errorCorrectionLevel: 'M',
                        color: { dark: '#000000', light: '#FFFFFF' }
                    });
                    connectionStatus = 'qr_ready';
                    console.log('[WhatsApp Bridge] New crisp high-res QR code generated.');
                } catch (err) {
                    console.error('[WhatsApp Bridge] Failed to generate QR data URL:', err);
                }
            }

            if (connection === 'close') {
                const statusCode = lastDisconnect?.error?.output?.statusCode;
                const shouldReconnect = statusCode !== DisconnectReason.loggedOut;
                console.log(`[WhatsApp Bridge] Connection closed (status: ${statusCode}). Reconnect: ${shouldReconnect}`);

                connectionStatus = 'disconnected';
                qrDataUrl = null;
                userInfo = null;

                if (shouldReconnect) {
                    setTimeout(connectToWhatsApp, 3000);
                } else {
                    console.log('[WhatsApp Bridge] Logged out. Clearing credentials...');
                    if (fs.existsSync(AUTH_DIR)) {
                        fs.rmSync(AUTH_DIR, { recursive: true, force: true });
                    }
                    setTimeout(connectToWhatsApp, 2000);
                }
            } else if (connection === 'open') {
                console.log('[WhatsApp Bridge] Connected successfully!');
                connectionStatus = 'connected';
                qrDataUrl = null;
                userInfo = sock.user;
            }
        });

        sock.ev.on('creds.update', saveCreds);

    } catch (err) {
        console.error('[WhatsApp Bridge] Error initializing Baileys:', err);
        lastError = err.message;
        connectionStatus = 'disconnected';
        setTimeout(connectToWhatsApp, 5000);
    }
}

// 1. Status Endpoint
app.get('/status', (req, res) => {
    res.json({
        status: connectionStatus,
        qr: qrDataUrl,
        user: userInfo,
        error: lastError
    });
});

// 2. Send Bill Endpoint
app.post('/send-bill', async (req, res) => {
    try {
        if (connectionStatus !== 'connected' || !sock) {
            return res.status(503).json({
                success: false,
                error: 'WhatsApp is not connected yet. Please link your device via QR code.'
            });
        }

        const { phone, message, pdfPath } = req.body;
        if (!phone) {
            return res.status(400).json({ success: false, error: 'Phone number is required.' });
        }

        // Format phone number to international format without + or spaces
        let cleanPhone = phone.toString().replace(/[^0-9]/g, '');
        if (cleanPhone.length === 10) {
            cleanPhone = '91' + cleanPhone; // Default to India country code
        }
        const jid = `${cleanPhone}@s.whatsapp.net`;

        let sentMessage = null;

        // If PDF path is provided and exists, send the document with caption
        if (pdfPath && fs.existsSync(pdfPath)) {
            const buffer = fs.readFileSync(pdfPath);
            const fileName = path.basename(pdfPath);
            sentMessage = await sock.sendMessage(jid, {
                document: buffer,
                mimetype: 'application/pdf',
                fileName: fileName,
                caption: message || ''
            });
        } else if (message) {
            // Text only
            sentMessage = await sock.sendMessage(jid, { text: message });
        }

        return res.json({
            success: true,
            phone: cleanPhone,
            messageId: sentMessage?.key?.id || null
        });

    } catch (err) {
        console.error('[WhatsApp Bridge] Error sending bill:', err);
        return res.status(500).json({
            success: false,
            error: err.message || 'Failed to send WhatsApp message.'
        });
    }
});

// 3. Logout Endpoint
app.post('/logout', async (req, res) => {
    try {
        if (sock) {
            await sock.logout();
        }
        if (fs.existsSync(AUTH_DIR)) {
            fs.rmSync(AUTH_DIR, { recursive: true, force: true });
        }
        connectionStatus = 'disconnected';
        qrDataUrl = null;
        userInfo = null;
        setTimeout(connectToWhatsApp, 1000);
        res.json({ success: true, message: 'Logged out successfully.' });
    } catch (err) {
        res.status(500).json({ success: false, error: err.message });
    }
});

// 4. Pairing Code Endpoint (Camera-less linking via 8-digit phone code)
app.post('/request-pairing-code', async (req, res) => {
    try {
        if (connectionStatus === 'connected') {
            return res.json({
                success: false,
                error: 'WhatsApp is already connected!'
            });
        }
        if (!sock) {
            return res.status(503).json({
                success: false,
                error: 'WhatsApp service is initializing. Please wait a few seconds and retry.'
            });
        }

        const { phone } = req.body;
        if (!phone) {
            return res.status(400).json({ success: false, error: 'Phone number is required.' });
        }

        let cleanPhone = phone.toString().replace(/[^0-9]/g, '');
        if (cleanPhone.length === 10) {
            cleanPhone = '91' + cleanPhone;
        }

        console.log(`[WhatsApp Bridge] Requesting pairing code for ${cleanPhone}...`);
        const code = await sock.requestPairingCode(cleanPhone);
        console.log(`[WhatsApp Bridge] Pairing code generated: ${code}`);

        return res.json({
            success: true,
            code: code,
            phone: cleanPhone
        });

    } catch (err) {
        console.error('[WhatsApp Bridge] Error requesting pairing code:', err);
        return res.status(500).json({
            success: false,
            error: err.message || 'Failed to request pairing code.'
        });
    }
});

// Start the Express server and WhatsApp client
app.listen(PORT, '127.0.0.1', () => {
    console.log(`[WhatsApp Bridge] Running on http://127.0.0.1:${PORT}`);
    connectToWhatsApp();
});

