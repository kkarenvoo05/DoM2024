import React from 'react';
import "./Results.css";
import { useLocation } from 'react-router-dom';

const Results = () => {
    const location = useLocation();
    const { patID, selectedPrompts, results } = location.state || {};

    return (
        <div className="results-container">
            <h1 className="page-title">Results</h1>
            <div className="results-content">
                <h2>Patient ID: {patID}</h2>
                <div className="prompts-results">
                    <table className="results-table">
                        <thead>
                            <tr>
                                <th>Prompt</th>
                                <th>Result</th>
                            </tr>
                        </thead>
                        <tbody>
                            {selectedPrompts.map((prompt, index) => (
                                <tr key={index}>
                                    <td>{prompt}</td>
                                    <td>{results[index]}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default Results;
