import React, { useState, useEffect } from 'react';
import config from '../config';
import './TemplateSender.css';

function TemplateSender() {
  const [users, setUsers] = useState([]);
  const [selectedUsers, setSelectedUsers] = useState([]);
  const [templateName, setTemplateName] = useState('');
  const [languageCode, setLanguageCode] = useState('en');
  const [components, setComponents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectAll, setSelectAll] = useState(false);

  // Fetch users on component mount
  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${config.API_URL}/api/users`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch users');
      }
      
      const data = await response.json();
      // Ensure we always set an array
      setUsers(Array.isArray(data) ? data : (data.users || []));
      setError('');
    } catch (err) {
      setError(`Failed to load users: ${err.message}`);
      console.error('Error fetching users:', err);
      setUsers([]); // Set empty array on error
    } finally {
      setLoading(false);
    }
  };

  const handleUserSelect = (phoneNumber) => {
    if (selectedUsers.includes(phoneNumber)) {
      setSelectedUsers(selectedUsers.filter(num => num !== phoneNumber));
    } else {
      setSelectedUsers([...selectedUsers, phoneNumber]);
    }
  };

  const handleSelectAll = () => {
    if (selectAll) {
      setSelectedUsers([]);
    } else {
      const filteredPhones = filteredUsers.map(user => user.whatsapp_phone);
      setSelectedUsers(filteredPhones);
    }
    setSelectAll(!selectAll);
  };

  const addComponent = (type) => {
    const newComponent = {
      type: type,
      parameters: []
    };

    if (type === 'body' || type === 'header') {
      newComponent.parameters.push({ type: 'text', text: '' });
    }

    setComponents([...components, newComponent]);
  };

  const removeComponent = (index) => {
    setComponents(components.filter((_, i) => i !== index));
  };

  const updateComponentParameter = (compIndex, paramIndex, field, value) => {
    const updatedComponents = [...components];
    if (!updatedComponents[compIndex].parameters[paramIndex]) {
      updatedComponents[compIndex].parameters[paramIndex] = { type: 'text' };
    }
    updatedComponents[compIndex].parameters[paramIndex][field] = value;
    setComponents(updatedComponents);
  };

  const addParameter = (compIndex) => {
    const updatedComponents = [...components];
    updatedComponents[compIndex].parameters.push({ type: 'text', text: '' });
    setComponents(updatedComponents);
  };

  const removeParameter = (compIndex, paramIndex) => {
    const updatedComponents = [...components];
    updatedComponents[compIndex].parameters = updatedComponents[compIndex].parameters.filter((_, i) => i !== paramIndex);
    setComponents(updatedComponents);
  };

  const handleSendTemplates = async () => {
    if (selectedUsers.length === 0) {
      setError('Please select at least one user');
      return;
    }

    if (!templateName.trim()) {
      setError('Please enter a template name');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    const results = {
      success: 0,
      failed: 0,
      errors: []
    };

    for (const phoneNumber of selectedUsers) {
      try {
        const messageData = {
          phone_number: phoneNumber,
          template_name: templateName,
          language_code: languageCode
        };

        // Only add components if they exist
        if (components.length > 0) {
          messageData.components = components;
        }

        const response = await fetch(`${config.API_URL}/messaging/send/template`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(messageData)
        });

        if (response.ok) {
          results.success++;
        } else {
          const errorData = await response.json();
          results.failed++;
          results.errors.push({
            phone: phoneNumber,
            error: errorData.detail || 'Unknown error'
          });
        }
      } catch (err) {
        results.failed++;
        results.errors.push({
          phone: phoneNumber,
          error: err.message
        });
      }
    }

    setLoading(false);

    if (results.success > 0) {
      setSuccess(`✅ Successfully sent ${results.success} template message(s)`);
    }

    if (results.failed > 0) {
      setError(`⚠️ Failed to send ${results.failed} message(s). Check console for details.`);
      console.error('Failed messages:', results.errors);
    }

    // Clear selections after sending
    setSelectedUsers([]);
    setSelectAll(false);
  };

  const filteredUsers = Array.isArray(users) 
    ? users.filter(user =>
        user.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.whatsapp_phone?.includes(searchTerm)
      )
    : [];

  return (
    <div className="template-sender">
      <h1>📤 Send Template Messages</h1>

      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}

      <div className="template-config">
        <h2>Template Configuration</h2>
        
        <div className="form-group">
          <label>Template Name *</label>
          <input
            type="text"
            value={templateName}
            onChange={(e) => setTemplateName(e.target.value)}
            placeholder="e.g., hello_world, order_confirmation"
          />
        </div>

        <div className="form-group">
          <label>Language Code</label>
          <input
            type="text"
            value={languageCode}
            onChange={(e) => setLanguageCode(e.target.value)}
            placeholder="e.g., en, en_US, hi"
          />
        </div>

        <div className="components-section">
          <h3>Template Components (Optional)</h3>
          <div className="component-buttons">
            <button onClick={() => addComponent('header')} className="add-component-btn">
              + Add Header
            </button>
            <button onClick={() => addComponent('body')} className="add-component-btn">
              + Add Body
            </button>
          </div>

          {components.map((component, compIndex) => (
            <div key={compIndex} className="component-card">
              <div className="component-header">
                <h4>{component.type.toUpperCase()}</h4>
                <button onClick={() => removeComponent(compIndex)} className="remove-btn">
                  ✕
                </button>
              </div>

              {component.parameters.map((param, paramIndex) => (
                <div key={paramIndex} className="parameter-row">
                  <input
                    type="text"
                    value={param.text || ''}
                    onChange={(e) => updateComponentParameter(compIndex, paramIndex, 'text', e.target.value)}
                    placeholder={`Parameter ${paramIndex + 1}`}
                  />
                  <button
                    onClick={() => removeParameter(compIndex, paramIndex)}
                    className="remove-param-btn"
                  >
                    −
                  </button>
                </div>
              ))}

              <button onClick={() => addParameter(compIndex)} className="add-param-btn">
                + Add Parameter
              </button>
            </div>
          ))}
        </div>
      </div>

      <div className="user-selection">
        <h2>Select Recipients</h2>
        
        <div className="search-bar">
          <input
            type="text"
            placeholder="🔍 Search users by name or phone..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div className="select-all-section">
          <label>
            <input
              type="checkbox"
              checked={selectAll}
              onChange={handleSelectAll}
            />
            Select All ({filteredUsers.length} users)
          </label>
          <span className="selected-count">
            {selectedUsers.length} user(s) selected
          </span>
        </div>

        <div className="users-list">
          {loading && <div className="loading">Loading users...</div>}
          
          {!loading && filteredUsers.length === 0 && (
            <div className="no-users">No users found</div>
          )}

          {!loading && filteredUsers.map((user) => (
            <div
              key={user.whatsapp_phone}
              className={`user-card ${selectedUsers.includes(user.whatsapp_phone) ? 'selected' : ''}`}
              onClick={() => handleUserSelect(user.whatsapp_phone)}
            >
              <input
                type="checkbox"
                checked={selectedUsers.includes(user.whatsapp_phone)}
                onChange={() => {}}
              />
              <div className="user-info">
                <div className="user-name">{user.name || 'N/A'}</div>
                <div className="user-phone">{user.whatsapp_phone}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="action-section">
        <button
          onClick={handleSendTemplates}
          disabled={loading || selectedUsers.length === 0 || !templateName}
          className="send-btn"
        >
          {loading ? 'Sending...' : `Send to ${selectedUsers.length} User(s)`}
        </button>
      </div>
    </div>
  );
}

export default TemplateSender;
