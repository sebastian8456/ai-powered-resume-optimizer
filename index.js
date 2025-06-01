import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import JobMatcher from './JobMatcher';
import MatchResultPage from './MatchResultPage';

const root = ReactDOM.createRoot(document.getElementById('root'));

root.render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<JobMatcher />} />
        <Route path="/match-result" element={<MatchResultPage />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
