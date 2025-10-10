import React, { useState } from 'react';
import './UpdateUserForm.css';

function UpdateUserForm() {
  const [searchPhone, setSearchPhone] = useState('');
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searching, setSearching] = useState(false);
  const [alert, setAlert] = useState(null);
  const [tagInput, setTagInput] = useState('');
  
  const [formData, setFormData] = useState({
    display_name: '',
    business_name: '',
    email: '',
    customer_tier: 'regular',
    tags: [],
    notes: '',
    subscription: 'subscribed'
  });

  // Search for user by phone number
  const handleSearch = async (e) => {
    e.preventDefault();
    
    if (!searchPhone.trim()) {
      setAlert({ type: 'error', message: '❌ Please enter a phone number' });
      return;
    }

    setSearching(true);
    setAlert(null);
    setUser(null);

    try {
      const response = await fetch(
        `https://hwwsxxpemc.us-east-1.awsapprunner.com/api/users/${encodeURIComponent(searchPhone.trim())}`
      );

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        
        // Populate form with user data
        setFormData({
          display_name: userData.display_name || '',
          business_name: userData.business_name || '',
          email: userData.email || '',
          customer_tier: userData.customer_tier || 'regular',
          tags: userData.tags || [],
          notes: userData.notes || '',
          subscription: userData.subscription || 'subscribed'
        });
        
        setAlert({ type: 'success', message: '✅ User found!' });
      } else if (response.status === 404) {
        setAlert({ type: 'error', message: '❌ User not found' });
      } else {
        const error = await response.json();
        setAlert({ type: 'error', message: `❌ Error: ${error.detail || 'Failed to fetch user'}` });
      }
    } catch (error) {
      setAlert({ 
        type: 'error', 
        message: `❌ Network Error: ${error.message}. Make sure backend is running.` 
      });
    } finally {
      setSearching(false);
    }
  };

  // Update user
  const handleUpdate = async (e) => {
    e.preventDefault();
    
    if (!user) {
      setAlert({ type: 'error', message: '❌ No user selected to update' });
      return;
    }

    setLoading(true);
    setAlert(null);

    // Prepare update data (only send changed fields)
    const updateData = {
      display_name: formData.display_name.trim() || null,
      business_name: formData.business_name.trim() || null,
      email: formData.email.trim() || null,
      customer_tier: formData.customer_tier,
      tags: formData.tags,
      notes: formData.notes.trim() || null,
      subscription: formData.subscription
    };

    try {
      const response = await fetch(
        `http://localhost:8000/api/users/${encodeURIComponent(user.whatsapp_phone)}`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(updateData)
        }
      );

      const result = await response.json();

      if (response.ok) {
        setAlert({ 
          type: 'success', 
          message: `✅ User "${user.whatsapp_phone}" updated successfully!` 
        });
        
        // Update the user state with new data
        setUser(result);
        
        // Refresh form with updated data
        setFormData({
          display_name: result.display_name || '',
          business_name: result.business_name || '',
          email: result.email || '',
          customer_tier: result.customer_tier || 'regular',
          tags: result.tags || [],
          notes: result.notes || '',
          subscription: result.subscription || 'subscribed'
        });
      } else {
        setAlert({ 
          type: 'error', 
          message: `❌ Update failed: ${result.detail || 'Unknown error'}` 
        });
      }
    } catch (error) {
      setAlert({ 
        type: 'error', 
        message: `❌ Network Error: ${error.message}` 
      });
    } finally {
      setLoading(false);
    }
  };

  // Handle form input changes
  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  // Tag management
  const handleAddTag = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      const tag = tagInput.trim();
      if (tag && !formData.tags.includes(tag)) {
        setFormData(prev => ({
          ...prev,
          tags: [...prev.tags, tag]
        }));
        setTagInput('');
      }
    }
  };

  const handleRemoveTag = (tagToRemove) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove)
    }));
  };

  // Reset form
  const handleReset = () => {
    setSearchPhone('');
    setUser(null);
    setFormData({
      display_name: '',
      business_name: '',
      email: '',
      customer_tier: 'regular',
      tags: [],
      notes: '',
      subscription: 'subscribed'
    });
    setAlert(null);
    setTagInput('');
  };

  return (
    <div className="update-user-container">
      <div className="update-form-card">
        <div className="form-header">
          <h1>🔄 Update User</h1>
          <p className="subtitle">Search and update customer information</p>
        </div>

        {alert && (
          <div className={`alert alert-${alert.type}`}>
            {alert.message}
          </div>
        )}

        {/* Search Section */}
        <form onSubmit={handleSearch} className="search-form">
          <div className="search-group">
            <label htmlFor="searchPhone">
              Search by Phone Number <span className="required">*</span>
            </label>
            <div className="search-input-group">
              <input
                type="tel"
                id="searchPhone"
                value={searchPhone}
                onChange={(e) => setSearchPhone(e.target.value)}
                placeholder="+1234567890"
                disabled={searching}
                className="search-input"
              />
              <button 
                type="submit" 
                className="btn btn-search"
                disabled={searching}
              >
                {searching ? '🔍 Searching...' : '🔍 Search'}
              </button>
            </div>
          </div>
        </form>

        {/* User Info Display */}
        {user && (
          <div className="user-info-card">
            <h3>📋 Current User Information</h3>
            <div className="user-info-grid">
              <div className="info-item">
                <span className="info-label">Phone:</span>
                <span className="info-value">{user.whatsapp_phone}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Display Name:</span>
                <span className="info-value">{user.display_name || 'N/A'}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Business:</span>
                <span className="info-value">{user.business_name || 'N/A'}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Email:</span>
                <span className="info-value">{user.email || 'N/A'}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Tier:</span>
                <span className={`tier-badge tier-${user.customer_tier}`}>
                  {user.customer_tier}
                </span>
              </div>
              <div className="info-item">
                <span className="info-label">Subscription:</span>
                <span className={`status-badge ${user.subscription === 'subscribed' ? 'subscribed' : 'unsubscribed'}`}>
                  {user.subscription === 'subscribed' ? '✅ Subscribed' : '❌ Unsubscribed'}
                </span>
              </div>
              <div className="info-item full-width">
                <span className="info-label">Total Messages:</span>
                <span className="info-value">{user.total_messages || 0}</span>
              </div>
              <div className="info-item full-width">
                <span className="info-label">Created:</span>
                <span className="info-value">
                  {user.created_at ? new Date(user.created_at).toLocaleString() : 'N/A'}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Update Form */}
        {user && (
          <form onSubmit={handleUpdate} className="update-form">
            <h3 className="form-section-title">✏️ Update Information</h3>
            
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="display_name">Display Name</label>
                <input
                  type="text"
                  id="display_name"
                  name="display_name"
                  value={formData.display_name}
                  onChange={handleInputChange}
                  placeholder="John Doe"
                  disabled={loading}
                />
              </div>

              <div className="form-group">
                <label htmlFor="business_name">Business Name</label>
                <input
                  type="text"
                  id="business_name"
                  name="business_name"
                  value={formData.business_name}
                  onChange={handleInputChange}
                  placeholder="Doe's Store"
                  disabled={loading}
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="email">Email</label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  placeholder="john@example.com"
                  disabled={loading}
                />
              </div>

              <div className="form-group">
                <label htmlFor="customer_tier">Customer Tier</label>
                <select
                  id="customer_tier"
                  name="customer_tier"
                  value={formData.customer_tier}
                  onChange={handleInputChange}
                  disabled={loading}
                >
                  <option value="regular">Regular</option>
                  <option value="premium">Premium</option>
                  <option value="vip">VIP</option>
                </select>
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="tagInput">Tags</label>
              <input
                type="text"
                id="tagInput"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyPress={handleAddTag}
                placeholder="Enter tag and press Enter"
                disabled={loading}
              />
              {formData.tags.length > 0 && (
                <div className="tags-display">
                  {formData.tags.map((tag, index) => (
                    <span key={index} className="tag">
                      {tag}
                      <button
                        type="button"
                        onClick={() => handleRemoveTag(tag)}
                        disabled={loading}
                        className="tag-remove"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="notes">Notes</label>
              <textarea
                id="notes"
                name="notes"
                value={formData.notes}
                onChange={handleInputChange}
                placeholder="Additional notes..."
                rows="4"
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  name="subscription"
                  checked={formData.subscription === 'subscribed'}
                  onChange={(e) => {
                    setFormData(prev => ({
                      ...prev,
                      subscription: e.target.checked ? 'subscribed' : 'unsubscribed'
                    }));
                  }}
                  disabled={loading}
                />
                <span>Subscribed to Template Messages</span>
              </label>
              <small className="help-text">
                Uncheck to unsubscribe user from template messages. Does NOT affect automated replies to their messages.
              </small>
            </div>

            <div className="button-group">
              <button
                type="submit"
                className="btn btn-primary"
                disabled={loading}
              >
                {loading ? '⏳ Updating...' : '✅ Update User'}
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={handleReset}
                disabled={loading}
              >
                🔄 Reset
              </button>
            </div>
          </form>
        )}

        {!user && !searching && (
          <div className="empty-state">
            <div className="empty-icon">🔍</div>
            <p>Search for a user by phone number to update their information</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default UpdateUserForm;
