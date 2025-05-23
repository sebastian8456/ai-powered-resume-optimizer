import React, { useState } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import './App.css';

function App() {
  const [resumeText, setResumeText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setIsLoading(true);
    try {
      if (file.type === 'application/pdf') {
        const formData = new FormData();
        formData.append('file', file);

        const response = await axios.post('http://localhost:8000/upload-resume', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        
        setResumeText(response.data.text);
        setMessage('PDF uploaded and parsed successfully!');
      } else {
        const reader = new FileReader();
        reader.onload = (event) => {
          setResumeText(event.target.result);
        };
        reader.readAsText(file);
      }
    } catch (error) {
      setMessage('Error uploading file: ' + error.message);
      console.error(error);
    } finally {
      setIsLoading(false);
    }
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

  const optimizeResume = async () => {
    setIsLoading(true);
    try {
        const response = await axios.post('http://localhost:8000/optimize-resume', {
            text: resumeText,
            id: null
        });
        
        // Update the resume text with the optimized version
        setResumeText(response.data.optimized_resume);
        
        // Set the markdown content directly
        setMessage(response.data.suggestions);
    } catch (error) {
        setMessage('Error optimizing resume: ' + error.message);
        console.error(error);
    } finally {
        setIsLoading(false);
    }
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
          {isLoading ? 'Optimizing...' : 'Optimize Resume'}
        </button>
      </div>

      {message && (
        <div className="message">
          <div className="suggestions">
            <ReactMarkdown>{message}</ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;