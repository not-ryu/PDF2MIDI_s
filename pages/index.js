import { useState, useRef, useEffect } from 'react';
import Image from 'next/image';

export default function Home() {
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState(null);
  const [convertedImage, setConvertedImage] = useState(null);
  const [logs, setLogs] = useState([]);
  const [isClearing, setIsClearing] = useState(false);

  const logContainerRef = useRef(null);

  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsUploading(true);
    setError(null);
    setLogs([]);

    const formData = new FormData();
    const fileInput = e.target.elements.pdfFile;

    if (!fileInput.files[0]) {
      setError('Please select a PDF file');
      setIsUploading(false);
      return;
    }

    formData.append('pdf', fileInput.files[0]);

    try {
      // First upload the file
      const uploadResponse = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      if (!uploadResponse.ok) {
        throw new Error(`Upload failed: ${uploadResponse.statusText}`);
      }

      const { sessionId } = await uploadResponse.json();

      // Then connect to SSE endpoint with the sessionId
      const eventSource = new EventSource(`/api/convert?sessionId=${sessionId}`);

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          setLogs(prevLogs => {
            const newLog = {
              id: Date.now(),
              type: data.type,
              message: data.message
            };
            return [...prevLogs, newLog];
          });

          if (data.type === 'complete') {
            eventSource.close();
            setIsUploading(false);
            if (data.imagePath) {
              setConvertedImage(data.imagePath);
              // Open new window with session images
              window.open(`/session-viewer?sessionId=${sessionId}`, '_blank');
            }
          } else if (data.type === 'error') {
            eventSource.close();
            setIsUploading(false);
            setError(data.message);
          }
        } catch (err) {
          console.error('Error parsing SSE data:', err);
        }
      };

      eventSource.onopen = () => {
        console.log('SSE connection opened');
        setLogs(prev => [...prev, {
          id: Date.now(),
          type: 'info',
          message: 'Connected to conversion service...'
        }]);
      };

      eventSource.onerror = (error) => {
        console.error('EventSource error:', error);
        eventSource.close();
        setIsUploading(false);
        setError('Connection error occurred');
      };

    } catch (err) {
      setError(err.message);
      setIsUploading(false);
    }
  };

  const handleClearTemp = async () => {
    if (isUploading) return;

    setIsClearing(true);
    try {
      const response = await fetch('/api/clear-temp', {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error('Failed to clear temp directory');
      }

      // Optional: Add to logs
      setLogs(prev => [...prev, {
        id: Date.now(),
        type: 'info',
        message: 'Temporary files cleared successfully'
      }]);
    } catch (error) {
      setError(error.message);
    } finally {
      setIsClearing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-8">
      <main className="max-w-3xl mx-auto">
        <h1 className="text-4xl font-bold text-gray-800 text-center mb-12 tracking-tight">
          PDF to MIDI Converter
        </h1>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 bg-white shadow-sm transition-all hover:border-blue-400 hover:bg-blue-50/50">
            <input
              type="file"
              name="pdfFile"
              accept=".pdf"
              className="w-full file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer"
              disabled={isUploading}
            />
          </div>

          <button
            type="submit"
            disabled={isUploading}
            className="w-full bg-blue-600 text-white px-6 py-3 rounded-xl font-semibold hover:bg-blue-700 disabled:opacity-50 transition-colors duration-200 shadow-sm"
          >
            {isUploading ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Converting...
              </span>
            ) : 'Convert PDF'}
          </button>
        </form>

        <div className="mt-4">
          <button
            type="button"
            onClick={handleClearTemp}
            disabled={isUploading || isClearing}
            className="w-full bg-red-600 text-white px-6 py-3 rounded-xl font-semibold hover:bg-red-700 disabled:opacity-50 transition-colors duration-200 shadow-sm"
          >
            {isClearing ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Clearing...
              </span>
            ) : 'Clear Temporary Files'}
          </button>
        </div>

        {error && (
          <div className="mt-6 p-4 bg-red-50 border border-red-200 text-red-700 rounded-xl shadow-sm">
            <div className="flex items-center">
              <svg className="h-5 w-5 text-red-400 mr-2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              {error}
            </div>
          </div>
        )}

        <div className="mt-10">
          <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center">
            <svg className="h-5 w-5 text-gray-500 mr-2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
              <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd" />
            </svg>
            Process Output
          </h2>
          <div
            ref={logContainerRef}
            className="bg-gray-900 text-gray-100 p-6 rounded-xl h-72 overflow-y-auto font-mono text-sm whitespace-pre-wrap shadow-lg border border-gray-800 max-w-4xl"
          >
            {logs.map((log) => (
              <div
                key={log.id}
                className={`${log.type === 'stderr' ? 'text-red-400' :
                  log.type === 'info' ? 'text-blue-400' :
                    'text-emerald-400'
                  } leading-tight`}
              >
                {log.message}
              </div>
            ))}
          </div>
        </div>

        {convertedImage && (
          <div className="mt-10">
            <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center">
              <svg className="h-5 w-5 text-gray-500 mr-2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd" />
              </svg>
              Converted Score
            </h2>
            <div className="rounded-xl overflow-hidden shadow-lg border border-gray-200">
              <Image
                src={convertedImage}
                alt="Converted musical score"
                width={800}
                height={600}
                className="w-full"
              />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
