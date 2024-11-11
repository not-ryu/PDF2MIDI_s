import path from 'path';
import fs from 'fs';

export default async function handler(req, res) {
    if (req.method !== 'GET') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    const { sessionId } = req.query;
    if (!sessionId) {
        return res.status(400).json({ error: 'Session ID is required' });
    }

    const tempDir = path.join(PROJECT_PATHS.ROOT, 'temp', sessionId);
    const inputDir = path.join(tempDir, 'in');
    const outputDir = path.join(tempDir, 'out');
    const finalOutputDir = path.join(tempDir, 'final_output');

    try {
        const images = {
            input: fs.readdirSync(inputDir).filter(file => file.endsWith('.png')),
            output: fs.readdirSync(outputDir).filter(file => file.endsWith('.png')),
            final: fs.readdirSync(finalOutputDir).filter(file => file.endsWith('.png'))
        };

        return res.status(200).json(images);
    } catch (error) {
        return res.status(500).json({ error: 'Failed to fetch images' });
    }
} 