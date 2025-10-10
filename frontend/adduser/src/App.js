import React, { useState } from 'react';
import './App.css';
import AddUserForm from './components/AddUserForm';
import UpdateUserForm from './components/UpdateUserForm';
import BulkImportUsers from './components/BulkImportUsers';

function App() {
  const [activeTab, setActiveTab] = useState('add'); // 'add', 'update', or 'bulk-import'

  return (
    <div className="App">
      <div className="tab-navigation">
        <button
          className={`tab-button ${activeTab === 'add' ? 'active' : ''}`}
          onClick={() => setActiveTab('add')}
        >
          ➕ Add User
        </button>
        <button
          className={`tab-button ${activeTab === 'update' ? 'active' : ''}`}
          onClick={() => setActiveTab('update')}
        >
          🔄 Update User
        </button>
        <button
          className={`tab-button ${activeTab === 'bulk-import' ? 'active' : ''}`}
          onClick={() => setActiveTab('bulk-import')}
        >
          📊 Bulk Import
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'add' && <AddUserForm />}
        {activeTab === 'update' && <UpdateUserForm />}
        {activeTab === 'bulk-import' && <BulkImportUsers />}
      </div>
    </div>
  );
}

export default App;
