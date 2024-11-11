export const config = {
    api: {
        bodyParser: false,
        maxDuration: 300,
    },
};

import fs from 'fs';
import path from 'path';
import { v4 as uuidv4 } from 'uuid';
import { PROJECT_PATHS } from '../../constants/paths';
import multer from 'multer';

// Configure multer
const configureMulter = (tempDir) => multer({
    dest: tempDir,
    limits: { fileSize: 10 * 1024 * 1024 }, // 10MB limit
});

// Create middleware handler
const runMiddleware = (req, res, fn) => {
    return new Promise((resolve, reject) => {
        fn(req, res, (result) => {
            if (result instanceof Error) {
                return reject(result);
            }
            return resolve(result);
        });
    });
};

export default async function handler(req, res) {
    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    // Create a unique working directory
    const sessionId = uuidv4();
    const tempDir = path.join(PROJECT_PATHS.ROOT, 'temp', sessionId);
    const pdfDir = path.join(tempDir, 'pdf');
    const inputDir = path.join(tempDir, 'in');
    const outputDir = path.join(tempDir, 'out');
    const finalOutputDir = path.join(tempDir, 'final_output');

    try {
        // Create directories
        fs.mkdirSync(pdfDir, { recursive: true });
        fs.mkdirSync(inputDir, { recursive: true });
        fs.mkdirSync(outputDir, { recursive: true });
        fs.mkdirSync(finalOutputDir, { recursive: true });

        // Configure multer with the pdf directory
        const upload = configureMulter(pdfDir);

        // Handle file upload with multer
        await runMiddleware(req, res, upload.single('pdf'));

        if (!req.file) {
            throw new Error('No PDF file uploaded');
        }

        // Return the sessionId for the client to use with the SSE endpoint
        res.status(200).json({
            sessionId,
            message: 'File uploaded successfully'
        });

    } catch (error) {
        console.error('Upload error:', error);
        res.status(500).json({ error: error.message });
    }
} 