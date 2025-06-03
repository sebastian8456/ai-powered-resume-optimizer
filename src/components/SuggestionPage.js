import React, { useState, useEffect } from 'react';
import { getSuggestions, addSuggestion, deleteSuggestion } from '../services/api';

const SuggestionPage = () => {
  const [suggestions, setSuggestions] = useState([]);
  const [newSuggestion, setNewSuggestion] = useState({ suggestion: '' });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchSuggestions();
  }, []);

  const fetchSuggestions = async () => {
    try {
      setLoading(true);
      const response = await getSuggestions();
      setSuggestions(response.data);
    } catch (error) {
      console.error('Error fetching suggestions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddSuggestion = async (e) => {
    e.preventDefault();
    try {
      await addSuggestion(newSuggestion);
      setNewSuggestion({ suggestion: '' });
      fetchSuggestions();
    } catch (error) {
      console.error('Error adding suggestion:', error);
    }
  };

  const handleDeleteSuggestion = async (id) => {
    try {
      await deleteSuggestion(id);
      fetchSuggestions();
    } catch (error) {
      console.error('Error deleting suggestion:', error);
    }
  };

  return (
    <div>
      <h1>Suggestions</h1>
      
      <form onSubmit={handleAddSuggestion}>
        <h2>Add New Suggestion</h2>
        <textarea
          value={newSuggestion.suggestion}
          onChange={(e) => setNewSuggestion({ suggestion: e.target.value })}
          placeholder="Enter suggestion"
          required
        />
        <button type="submit">Add Suggestion</button>
      </form>

      <h2>Existing Suggestions</h2>
      {loading ? (
        <p>Loading...</p>
      ) : (
        <div>
          {suggestions.map((suggestion) => (
            <div key={suggestion.id} className="item">
              <p>{suggestion.suggestion}</p>
              <button onClick={() => handleDeleteSuggestion(suggestion.id)}>Delete</button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SuggestionPage;