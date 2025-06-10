import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';

function OptimizedResume() {
  const location = useLocation();
  const navigate = useNavigate();
  const optimizedText = location.state?.optimizedText;

  // Redirect to homepage if no resume text passed
  if (!optimizedText) {
    navigate('/');
    return null;
  }

  const handleExport = async () => {
    try {
      const response = await axios.post(
        'http://localhost:8000/export-resume',
        { text: optimizedText },
        { responseType: 'blob' }
      );

      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'optimized_resume.pdf');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting resume:', error);
      alert('Failed to download resume. Please try again.');
    }
  };

  return (
    <div className="optimized-container" style={{ padding: '2rem' }}>
      <h1 style={{ textAlign: 'center' }}>Optimized Resume</h1>

      <pre style={{
        whiteSpace: 'pre-wrap',
        fontFamily: 'monospace',
        lineHeight: '1.6',
        backgroundColor: '#f9f9f9',
        padding: '2rem',
        borderRadius: '8px',
        fontSize: '14px'
      }}>
        {optimizedText}
      </pre>

      <div style={{ display: 'flex', justifyContent: 'center', marginTop: '20px' }}>
        <button
          onClick={handleExport}
          style={{
            padding: '10px 20px',
            borderRadius: '6px',
            border: 'none',
            backgroundColor: '#17a2b8',
            color: '#fff',
            fontWeight: 'bold',
            cursor: 'pointer',
            marginRight: '10px'
          }}
        >
          Download PDF
        </button>

        <button
          onClick={() => navigate('/')}
          style={{
            padding: '10px 20px',
            borderRadius: '6px',
            border: 'none',
            backgroundColor: '#007bff',
            color: '#fff',
            fontWeight: 'bold',
            cursor: 'pointer'
          }}
        >
          Back
        </button>
      </div>
    </div>
  );
}

export default OptimizedResume;