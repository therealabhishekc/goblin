import React, { useState } from 'react';
import './App.css';
import AddUserForm from './components/AddUserForm';
import UpdateUserForm from './components/UpdateUserForm';

function App() {
  const [activeTab, setActiveTab] = useState('add'); // 'add' or 'update'

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
      </div>

      <div className="tab-content">
        {activeTab === 'add' ? <AddUserForm /> : <UpdateUserForm />}
      </div>
    </div>
  );
}

export default App;
