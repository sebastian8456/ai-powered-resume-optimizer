import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import './App.css';
import { useNavigate } from 'react-router-dom';
import { useResume } from './ResumeContext';

function App() {
  const { resumeText, setResumeText } = useResume();
  const [isLoading, setIsLoading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [message, setMessage] = useState('');
  // New state for structured suggestions
  const [suggestions, setSuggestions] = useState({
    summary: [],
    experience: [],
    education: [],
    skills: [],
    other: []
  });
  const [isExporting, setIsExporting] = useState(false);
  
  // Auth state
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [showLogin, setShowLogin] = useState(true); // true for login, false for register
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [authMessage, setAuthMessage] = useState('');
  const [accessToken, setAccessToken] = useState('');
  const [loggedInUsername, setLoggedInUsername] = useState(''); // Store logged in username
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const [isMatching, setIsMatching] = useState(false);
  const [optimizedText, setOptimizedText] = useState('');

  // Check if user is already logged in on component mount
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const savedUsername = localStorage.getItem('username');
    if (token) {
      setAccessToken(token);
      setIsLoggedIn(true);
      if (savedUsername) {
        setLoggedInUsername(savedUsername);
      }
    }
  }, []);

  // Set up axios interceptor to include token in requests
  useEffect(() => {
    if (accessToken) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`;
    } else {
      delete axios.defaults.headers.common['Authorization'];
    }
  }, [accessToken]);

  const handleRegister = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await axios.post('http://localhost:8000/register', {
        username,
        password
      });
      setAuthMessage('Registration successful! Please login.');
      setShowLogin(true);
      setUsername('');
      setPassword('');
    } catch (error) {
      setAuthMessage('Registration failed: ' + (error.response?.data?.detail || error.message));
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      const response = await axios.post('http://localhost:8000/login', {
        username,
        password
      });
      
      const token = response.data.access_token;
      setAccessToken(token);
      setLoggedInUsername(username); // Store the logged in username
      localStorage.setItem('access_token', token);
      localStorage.setItem('username', username); // Store username in localStorage
      setIsLoggedIn(true);
      setAuthMessage('Login successful!');
      setUsername(''); // Clear form
      setPassword(''); // Clear form
    } catch (error) {
      setAuthMessage('Login failed: ' + (error.response?.data?.detail || error.message));
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await axios.post('http://localhost:8000/logout');
    } catch (error) {
      console.log('Logout request failed, but continuing with local logout');
    }
    
    setAccessToken('');
    setLoggedInUsername('');
    localStorage.removeItem('access_token');
    localStorage.removeItem('username');
    setIsLoggedIn(false);
    setResumeText('');
    setMessage('');
    setAuthMessage('Logged out successfully');
  };

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
      if (error.response?.status === 401) {
        setMessage('Please login to upload resumes');
        handleLogout();
      } else {
        setMessage('Error uploading file: ' + error.message);
      }
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const generateExampleResume = async () => {
    setIsGenerating(true);
    try {
      const response = await axios.get('http://localhost:8000/create-resume');
      setResumeText(response.data['New resume: ']);
      setMessage('Example resume generated!');
    } catch (error) {
      if (error.response?.status === 401) {
        setMessage('Please login to generate resumes');
        handleLogout();
      } else {
        setMessage('Error generating resume');
      }
      console.error(error);
    } finally {
      setIsGenerating(false);
    }
  };

  const optimizeResume = async () => {
    setIsOptimizing(true);
    try {
        const response = await axios.post('http://localhost:8000/optimize-resume', {
            text: resumeText,
            id: null
        });
        
        if (response.data && response.data.suggestions) {
            const fullSuggestions = response.data.suggestions;
const splitIndex = fullSuggestions.indexOf('## OPTIMIZED VERSION');
const cleanSuggestions = splitIndex !== -1 ? fullSuggestions.slice(0, splitIndex).trim() : fullSuggestions;

setSuggestions(cleanSuggestions);
            setOptimizedText(response.data.optimized_resume);
            setMessage('Resume analyzed! Click on suggestions below to apply them.');
        } else {
            setMessage('Error: Invalid response format from server');
        }
    } catch (error) {
        if (error.response?.status === 401) {
          setMessage('Please login to optimize resumes');
          handleLogout();
        } else {
          setMessage('Error optimizing resume: ' + (error.response?.data?.detail || error.message));
        }
        console.error(error);
    } finally {
        setIsOptimizing(false);
    }
  };

  const applySuggestion = (suggestion) => {
    if (suggestion.original) {
      setResumeText(prevText => {
        const newText = prevText.replace(suggestion.original, suggestion.improved);
        return newText;
      });
    } else {
      setResumeText(prevText => {
        const newText = prevText.trim() + '\n\n' + suggestion.improved;
        return newText;
      });
    }
  };

  
  const handleExportResume = async () => {
    setIsExporting(true);
    try {
      console.log('Sending resume text:', resumeText);
      
      const response = await axios.post('http://localhost:8000/export-resume', {
        text: resumeText
      }, {
        responseType: 'blob'
      });
      
      console.log('Received response:', response);
      
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'resume.pdf');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      setMessage('Resume downloaded successfully!');
    } catch (error) {
      console.error('Export error:', error);
      console.error('Error response:', error.response);
      setMessage('Error exporting resume: ' + (error.response?.data?.detail || error.message));
    } finally {
      setIsExporting(false);
    }
  };


  const matchJobs = async () => {
  setIsMatching(true);
  setError(null);

  try {
    const response = await fetch("http://127.0.0.1:8000/match-jobs/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${accessToken}`
      },
      body: JSON.stringify({ text: resumeText }),
    });

    if (!response.ok) {
      const errData = await response.json();
      throw new Error(errData.detail || "Failed to fetch job posting");
    }

    const data = await response.json();
    console.log("BACKEND RESPONSE:", data); // Add this line
    navigate("/match-result", { state: { jobPosting: data } });
  } catch (err) {
    setError(err.message);
    console.error("Match jobs error:", err);
  } finally {
    setIsMatching(false);
  }
};



  // If not logged in, show auth form
  if (!isLoggedIn) {
    return (
      <div className="app">
        <h1>AI-Powered Resume Optimizer</h1>
        
        <div className="auth-container">
          <div className="auth-toggle">
            <button 
              className={showLogin ? 'active' : ''} 
              onClick={() => setShowLogin(true)}
            >
              Login
            </button>
            <button 
              className={!showLogin ? 'active' : ''} 
              onClick={() => setShowLogin(false)}
            >
              Register
            </button>
          </div>

          <form onSubmit={showLogin ? handleLogin : handleRegister}>
            <h2>{showLogin ? 'Login' : 'Register'}</h2>
            
            <div className="form-group">
              <label>Username:</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </div>
            
            <div className="form-group">
              <label>Password:</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            
            <button type="submit" disabled={isLoading}>
              {isLoading ? 'Processing...' : (showLogin ? 'Login' : 'Register')}
            </button>
          </form>

          {authMessage && (
            <div className="auth-message">
              {authMessage}
            </div>
          )}
        </div>
      </div>
    );
  }

  // If logged in, show main app
  // If logged in, show main app
  return (
    <div className="app">
      <div className="header">
        <h1>AI-Powered Resume Optimizer</h1>
        <div className="user-info">
          <span>Welcome, {loggedInUsername}!</span>
          <button onClick={handleLogout} className="logout-btn">
            Logout
          </button>
        </div>
      </div>
      
      <div className="resume-actions">
        <div className="upload-section">
          <h2>Upload Your Resume</h2>
          <input type="file" accept=".txt,.pdf,.docx" onChange={handleFileUpload} />
        </div>
        
        <div className="generate-section">
          <h2>Or Generate Example</h2>
          <button onClick={generateExampleResume} disabled={isGenerating}>
            {isGenerating ? 'Generating...' : 'Generate Example Resume'}
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
          disabled={!resumeText || isOptimizing}
        >
          {isOptimizing ? 'Optimizing...' : 'Optimize Resume'}
        </button>
        
        <button
          onClick={matchJobs}
          disabled={!resumeText || isOptimizing}
        >
          {isMatching ? 'Matching...' : 'Match Jobs'}
        </button>

        <button
          onClick={handleExportResume}
          disabled={!resumeText || isExporting}
          className="export-btn"
        >
          {isExporting ? 'Exporting...' : 'Save & Export Resume'}
        </button>
      </div>

      {message && (
        <div className="message">
          <p>{message}</p>
        </div>
      )}

      {/* Suggestions Section */}
     {typeof suggestions === 'string' && !suggestions.includes('OPTIMIZED VERSION') && (
  <div className="suggestions-container">
    <h2>Optimization Suggestions</h2>
    <ReactMarkdown>{suggestions}</ReactMarkdown>
  </div>
)}

      {optimizedText && (
        <div style={{ marginTop: '30px', textAlign: 'center' }}>
          <button
            onClick={() => navigate('/optimized', { state: { optimizedText } })}
            style={{
              padding: '12px 24px',
              fontSize: '16px',
              fontWeight: 'bold',
              borderRadius: '8px',
              backgroundColor: '#28a745',
              color: 'white',
              border: 'none',
              cursor: 'pointer'
            }}
          >
            Apply All Suggestions
          </button>
        </div>
      )}

    </div>
  );
}

export default App;