import React, { useState, useEffect } from 'react';
import './App.css';
import TemplateList from './components/TemplateList';
import TemplateForm from './components/TemplateForm';
import { getTemplates, createTemplate, updateTemplate, deleteTemplate } from './api/templateApi';

function App() {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getTemplates();
      setTemplates(data);
    } catch (err) {
      setError(err.message || 'Failed to load templates');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (templateData) => {
    try {
      await createTemplate(templateData);
      await loadTemplates();
      setShowForm(false);
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to create template');
      throw err;
    }
  };

  const handleUpdate = async (id, templateData) => {
    try {
      await updateTemplate(id, templateData);
      await loadTemplates();
      setEditingTemplate(null);
      setShowForm(false);
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to update template');
      throw err;
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this template?')) {
      return;
    }
    try {
      await deleteTemplate(id);
      await loadTemplates();
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to delete template');
    }
  };

  const handleEdit = (template) => {
    setEditingTemplate(template);
    setShowForm(true);
  };

  const handleCancelEdit = () => {
    setEditingTemplate(null);
    setShowForm(false);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>📋 WhatsApp Template Manager</h1>
        <p>Manage interactive menu templates for WhatsApp conversations</p>
      </header>

      <main className="App-main">
        {error && (
          <div className="error-banner">
            <span>⚠️ {error}</span>
            <button onClick={() => setError(null)}>✕</button>
          </div>
        )}

        <div className="action-bar">
          {!showForm && (
            <button 
              className="btn btn-primary"
              onClick={() => setShowForm(true)}
            >
              ➕ Create New Template
            </button>
          )}
        </div>

        {showForm && (
          <TemplateForm
            template={editingTemplate}
            onSubmit={editingTemplate ? 
              (data) => handleUpdate(editingTemplate.id, data) : 
              handleCreate
            }
            onCancel={handleCancelEdit}
          />
        )}

        {loading ? (
          <div className="loading">Loading templates...</div>
        ) : (
          <TemplateList
            templates={templates}
            onEdit={handleEdit}
            onDelete={handleDelete}
          />
        )}
      </main>
    </div>
  );
}

export default App;
