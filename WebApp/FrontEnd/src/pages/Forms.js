import React, { useState, useEffect } from "react";
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import "./Forms.css";

const Forms = () => {
  const [patID, setPatID] = useState(1);
  const [prompts, setPrompts] = useState([]);
  const [selectedPrompts, setSelectedPrompts] = useState([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    async function fetchItems() {
      try {
        const response = await axios.get('http://localhost:5001/prompts');
        setPrompts(response.data);
      } catch (error) {
        console.error('Error fetching items:', error);
        setError('Failed to fetch prompts. Please try again later.');
      }
    }
    fetchItems();
  }, []);

  const handleCheckboxChange = (prompt) => {
    setSelectedPrompts(prevSelected => 
      prevSelected.includes(prompt)
        ? prevSelected.filter(p => p !== prompt)
        : [...prevSelected, prompt]
    );
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);

    console.log('Selected Patient:', patID);
    console.log('Selected Prompts:', selectedPrompts);

    try {
      const response = await axios.post('http://localhost:5001/submit', {
        patID,
        selectedPrompts
      });
      
      navigate('/results', { state: response.data });
    } catch (error) {
      console.error('Error submitting data:', error);
      setError('Failed to submit data. Please try again.');
    } finally {
      setIsSubmitting(false);
    }

    // try {
    //   const response = await fetch('/submit', {
    //     method: 'POST',
    //     headers: { 'Content-Type': 'application/json' },
    //     body: JSON.stringify({ patID, selectedPrompts })
    //   });
    //   if (response.ok) {
    //     const result = await response.json();
    //     navigate('/results', { state: result });
    //   } else {
    //     console.error('Submission failed');
    //   }
    // } catch (error) {
    //   console.error('Error submitting form:', error);
    // }
  };

  if (error) {
    return <div className="error-message">{error}</div>;
  }

  return (
    <div className="forms-container">
      <h1 className="page-title">Data Submission</h1>
      <form onSubmit={handleSubmit}>
        <div className="patient-select">
          <label htmlFor="patient-id">Patient ID:</label>
          <select
            id="patient-id"
            value={patID}
            onChange={(e) => setPatID(parseInt(e.target.value))}
          >
            {Array.from({ length: 20 }, (_, i) => i + 1).map(num => (
              <option key={num} value={num}>{num}</option>
            ))}
          </select>
        </div>
        <h2 className="section-title">Select prompts to extract:</h2>
        <div className="prompts-container">
          <div className="checkbox-list">
            {prompts.map(prompt => (
              <div key={prompt} className="checkbox-item">
                <input
                  type="checkbox"
                  id={prompt}
                  value={prompt}
                  onChange={() => handleCheckboxChange(prompt)}
                  checked={selectedPrompts.includes(prompt)}
                />
                <label htmlFor={prompt}>{prompt}</label>
              </div>
            ))}
          </div>
          <div className="selected-items">
            <h3>Selected Prompts</h3>
            <ul>
              {selectedPrompts.map(prompt => (
                <li key={prompt}>{prompt}</li>
              ))}
            </ul>
          </div>
        </div>
        <button type="submit" className="submit-button" disabled={isSubmitting}>
          {isSubmitting ? 'Submitting...' : 'Submit'}
        </button>
      </form>
    </div>
  );
};

export default Forms;
