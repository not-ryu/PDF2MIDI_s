# PDF to MIDI Converter

### Node.js and npm Installation

This project requires node.js and npm, as well as [MuseScore](https://musescore.org/).

### Dependencies
1. **Install Python requirements**:
    ```bash
    pip3 install -r MIDI_Scripts/requirements.txt
    ```

    This will install the following dependencies:
    ```
    music21>=8.1.0
    numpy>=1.24.0
    opencv-python>=4.8.0
    PyMuPDF>=1.23.0
    scikit-learn>=1.3.0
    scipy>=1.11.0
    ```
    **Configure music21**:
    Run the configuration assistant:
    ```bash
    python3 -m music21.configure
    ```

    verify that `musicxmlPath` and `musescoreDirectPNGPath` are set correctly in `~/.music21rc`:
    ```bash
    cat ~/.music21rc
    ``` 
    should display something like   
    ``` xml
    ...
    <preference name="musescoreDirectPNGPath" value="/Applications/MuseScore 4.app/Contents/MacOS/mscore" />
    <preference name="musicxmlPath" value="/Applications/MuseScore 4.app" />
    ...
    ```


2. **Install npm packages**:
    ```bash
    npm install
    ```

    This will install the following dependencies from package.json:
    ```json
    {
        "dependencies": {
        "formidable": "^3.5.2",
        "multer": "^1.4.5-lts.1",
        "next": "15.0.3",
        "pdf2img": "^0.5.0",
        "react": "19.0.0-rc-66855b96-20241106",
        "react-dom": "19.0.0-rc-66855b96-20241106",
        "uuid": "^11.0.2"
        },
        "devDependencies": {
        "postcss": "^8",
        "tailwindcss": "^3.4.1"
        }
    }
    ```

3. **Start the development server**:
    ```bash
    npm run dev
    ```

    This will start the Next.js development server. By default, the application will be available at http://localhost:3000
