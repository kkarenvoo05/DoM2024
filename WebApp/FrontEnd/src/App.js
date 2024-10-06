import { Routes, Route } from 'react-router-dom';
import Home from './pages/Home.js';
import Forms from './pages/Forms.js';
import Results from './pages/Results.js';
import NoPage from './pages/NoPage.js';
import "./App.css";

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <Routes>
          <Route index element = {<Home />} />
          <Route path = "/" element = {<Home />} />
          <Route path = "/home" element = {<Home />} />
          <Route path = "/forms" element = {<Forms />} />
          <Route path = "/results" element = {<Results />} />
          <Route path = "*" element = {<NoPage />} />
        </Routes>
      </header>
    </div>
  );
}

export default App;
