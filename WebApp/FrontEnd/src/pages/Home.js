import React from 'react';
import "./Home.css";
import { useNavigate } from 'react-router-dom';

const Home = () => {
  const navigate = useNavigate();

  const handleNext = () => {
    navigate('/forms');
  };

  return (
    <div>
        <h1 className="fade-in-1">Welcome to Epixtract</h1>
        <p className="fade-in-2">An AI-powered tool to make data extraction easy</p>
        <p className="fade-in-3">To get started, select a database.</p>

        <div className="fade-in-4">
            <button className="fade-in-left fade-in-left-1" onClick={handleNext}>BMT</button>
            <button className="fade-in-left fade-in-left-2">AML</button>
        </div>
        
    </div>
  );
};

export default Home;
