/**
 * Main App Component
 * Campaign Manager Application
 */
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import CampaignList from './components/CampaignList';
import CreateCampaign from './components/CreateCampaign';
import CampaignDetails from './components/CampaignDetails';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        {/* Header/Navigation */}
        <header className="app-header">
          <div className="container">
            <h1>📱 Campaign Manager</h1>
            <nav className="nav-links">
              <Link to="/" className="nav-link">Campaigns</Link>
              <Link to="/create" className="nav-link">Create Campaign</Link>
            </nav>
          </div>
        </header>

        {/* Main Content */}
        <main className="app-main">
          <Routes>
            <Route path="/" element={<CampaignList />} />
            <Route path="/create" element={<CreateCampaign />} />
            <Route path="/campaign/:id" element={<CampaignDetails />} />
          </Routes>
        </main>

        {/* Footer */}
        <footer className="app-footer">
          <div className="container">
            <p>WhatsApp Marketing Campaign Manager</p>
          </div>
        </footer>
      </div>
    </Router>
  );
}

export default App;
