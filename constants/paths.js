import path from 'path';

// Get the project root directory, going up one level from __dirname since we're in constants/
const projectRoot = path.resolve(process.cwd());

export const PROJECT_PATHS = {
    ROOT: projectRoot,
    // Go up from the current directory to the project root, then into MIDI_Scripts
    MIDI_SCRIPTS: path.resolve(projectRoot, 'MIDI_Scripts')
};

// Add some debug validation
if (!require('fs').existsSync(PROJECT_PATHS.MIDI_SCRIPTS)) {
    console.error('WARNING: MIDI_Scripts directory not found at:', PROJECT_PATHS.MIDI_SCRIPTS);
} 