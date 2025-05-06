import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [resumeText, setResumeText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    const reader = new FileReader();
    reader.onload = (event) => {
      setResumeText(event.target.result);
    };
    reader.readAsText(file);
  };

  const generateExampleResume = async () => {
    setIsLoading(true);
    try {
      const response = await axios.get('http://localhost:8000/create-resume');
      setResumeText(response.data['New resume: ']);
      setMessage('Example resume generated!');
    } catch (error) {
      setMessage('Error generating resume');
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const optimizeResume = () => {
    // Placeholder for future optimization functionality
    setMessage('Optimization feature coming soon!');
  };

  return (
    <div className="app">
      <h1>AI-Powered Resume Optimizer</h1>
      
      <div className="resume-actions">
        <div className="upload-section">
          <h2>Upload Your Resume</h2>
          <input type="file" accept=".txt,.pdf,.docx" onChange={handleFileUpload} />
        </div>
        
        <div className="generate-section">
          <h2>Or Generate Example</h2>
          <button onClick={generateExampleResume} disabled={isLoading}>
            {isLoading ? 'Generating...' : 'Generate Example Resume'}
          </button>
        </div>
      </div>

      <div className="resume-display">
        <h2>Your Resume</h2>
        <textarea
          value={resumeText}
          onChange={(e) => setResumeText(e.target.value)}
          placeholder="Your resume will appear here..."
        />
      </div>

      <div className="optimize-section">
        <button 
          onClick={optimizeResume} 
          disabled={!resumeText || isLoading}
        >
          Optimize Resume
        </button>
      </div>

      {message && <div className="message">{message}</div>}
    </div>
  );
}

export default App;