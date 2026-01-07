import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Settings from './pages/Settings';
import TemplateManagement from './pages/templates/TemplateManagement';
import './styles/glassmorphism.css';

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <Router>
          <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route
            path="/dashboard"
            element={
              <Layout>
                <Dashboard />
              </Layout>
            }
          />
          <Route
            path="/messages"
            element={
              <Layout>
                <div className="glass-card">
                  <h1 className="text-gradient">Messages</h1>
                  <p>Messages page coming soon...</p>
                </div>
              </Layout>
            }
          />
          <Route
            path="/campaigns"
            element={
              <Layout>
                <div className="glass-card">
                  <h1 className="text-gradient">Campaigns</h1>
                  <p>Campaigns page coming soon...</p>
                </div>
              </Layout>
            }
          />
          <Route
            path="/templates"
            element={
              <Layout>
                <TemplateManagement />
              </Layout>
            }
          />
          <Route
            path="/users"
            element={
              <Layout>
                <div className="glass-card">
                  <h1 className="text-gradient">Users</h1>
                  <p>Users page coming soon...</p>
                </div>
              </Layout>
            }
          />
          <Route
            path="/analytics"
            element={
              <Layout>
                <div className="glass-card">
                  <h1 className="text-gradient">Analytics</h1>
                  <p>Analytics page coming soon...</p>
                </div>
              </Layout>
            }
          />
          <Route
            path="/archive"
            element={
              <Layout>
                <div className="glass-card">
                  <h1 className="text-gradient">Archive</h1>
                  <p>Archive page coming soon...</p>
                </div>
              </Layout>
            }
          />
          <Route
            path="/settings"
            element={
              <Layout>
                <Settings />
              </Layout>
            }
          />
        </Routes>
      </Router>
    </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
