export const config = {
    api: {
        bodyParser: false,
        maxDuration: 300,
    },
};

import fs from 'fs';
import path from 'path';
import { spawn } from 'child_process';
import { PROJECT_PATHS } from '../../constants/paths';
import { PassThrough } from 'stream';

export default async function handler(req, res) {
    if (req.method !== 'GET') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    const { sessionId } = req.query;

    if (!sessionId) {
        return res.status(400).json({ error: 'Session ID is required' });
    }

    const tempDir = path.join(PROJECT_PATHS.ROOT, 'temp', sessionId);
    const pdfDir = path.join(tempDir, 'pdf');
    const inputDir = path.join(tempDir, 'in');
    const outputDir = path.join(tempDir, 'out');
    const finalOutputDir = path.join(tempDir, 'final_output');

    // Verify the session exists
    if (!fs.existsSync(tempDir)) {
        return res.status(404).json({ error: 'Session not found' });
    }

    try {
        // Find the PDF file in the pdf directory
        const pdfFiles = fs.readdirSync(pdfDir);
        if (pdfFiles.length === 0) {
            throw new Error('No PDF file found in session');
        }
        const pdfPath = path.join(pdfDir, pdfFiles[0]);

        // Setup SSE response headers
        res.setHeader('Content-Type', 'text/event-stream');
        res.setHeader('Cache-Control', 'no-cache');
        res.setHeader('Connection', 'keep-alive');

        const responseStream = new PassThrough();
        responseStream.pipe(res);

        // First Python process (convert_best.py)
        const pythonProcess = spawn('python3', [
            '-u',
            path.resolve(PROJECT_PATHS.MIDI_SCRIPTS, 'convert_best.py'),
            pdfPath,
            '',
            inputDir
        ]);

        pythonProcess.stdout.on('data', (data) => {
            console.log('Python stdout:', data.toString());
            responseStream.write(`data: ${JSON.stringify({ type: 'stdout', message: data.toString() })}\n\n`);
            res.flush();
        });

        pythonProcess.stderr.on('data', (data) => {
            console.error('Python stderr:', data.toString());
            responseStream.write(`data: ${JSON.stringify({ type: 'stderr', message: data.toString() })}\n\n`);
            res.flush();
        });

        // Wait for first process to complete
        await new Promise((resolve, reject) => {
            pythonProcess.on('close', (code) => {
                if (code === 0) {
                    responseStream.write(`data: ${JSON.stringify({ type: 'status', message: 'First conversion complete' })}\n\n`);
                    resolve();
                } else {
                    reject(new Error(`Python process exited with code ${code}`));
                }
            });
            pythonProcess.on('error', (error) => {
                console.error('Process error:', error);
                reject(error);
            });
        });

        // Get the first converted image
        const images = fs.readdirSync(inputDir).filter(file => file.endsWith('.png'));
        if (images.length === 0) {
            throw new Error('No images were generated');
        }

        // Second Python process (final.py)
        const finalProcess = spawn('python3', [
            '-u',
            path.resolve(PROJECT_PATHS.MIDI_SCRIPTS, 'final.py'),
            tempDir
        ]);

        // Wait for second process to complete
        await new Promise((resolve, reject) => {
            finalProcess.on('close', (code) => {
                if (code === 0) {
                    const imagePath = `/api/images/${sessionId}/in/${images[0]}`;
                    responseStream.write(`data: ${JSON.stringify({
                        type: 'complete',
                        message: 'Conversion complete',
                        imagePath: imagePath
                    })}\n\n`);
                    responseStream.end();
                    resolve();
                } else {
                    reject(new Error(`Final process exited with code ${code}`));
                }
            });
            finalProcess.stderr.on('data', (data) => {
                console.error('Python stderr:', data.toString());
                responseStream.write(`data: ${JSON.stringify({ type: 'stderr', message: data.toString() })}\n\n`);
                res.flush();
            });
            finalProcess.stdout.on('data', (data) => {
                console.log('Python stdout:', data.toString());
                responseStream.write(`data: ${JSON.stringify({ type: 'stdout', message: data.toString() })}\n\n`);
                res.flush();
            });
            finalProcess.on('error', (error) => {
                console.error('Process error:', error);
                reject(error);
            });
        });

    } catch (error) {
        console.error('Conversion error:', error);
        const errorMessage = `data: ${JSON.stringify({ type: 'error', message: error.message })}\n\n`;
        if (!res.writableEnded) {
            res.write(errorMessage);
            res.end();
        }
    }
}