import fs from 'fs';
import path from 'path';
import { PROJECT_PATHS } from '../../constants/paths';

export default async function handler(req, res) {
    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    try {
        const tempDir = path.join(PROJECT_PATHS.ROOT, 'temp');

        // Check if temp directory exists
        if (fs.existsSync(tempDir)) {
            // Read all directories in temp
            const directories = fs.readdirSync(tempDir);

            // Delete each directory
            for (const dir of directories) {
                const dirPath = path.join(tempDir, dir);
                fs.rmSync(dirPath, { recursive: true, force: true });
            }
        }

        res.status(200).json({ message: 'Temp directory cleared successfully' });
    } catch (error) {
        console.error('Error clearing temp directory:', error);
        res.status(500).json({ error: 'Failed to clear temp directory' });
    }
} 