import React from 'react';
import { formatToCST } from '../utils/dateFormatter';

function UpdateUserFormView({
  searchPhone,
  setSearchPhone,
  user,
  searching,
  alert,
  formData,
  tagInput,
  setTagInput,
  loading,
  handleSearch,
  handleUpdate,
  handleInputChange,
  handleAddTag,
  handleRemoveTag,
  handleReset
}) {
  return (
    <div className="update-user-container">
      <div className="update-form-card">
        <div className="form-header">
          <h1>🔄 Update User</h1>
          <p className="subtitle">Search and update customer information</p>
        </div>

        {/* Alert Messages */}
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
                <span className="info-label">Email:</span>
                <span className="info-value">{user.email || 'N/A'}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Tier:</span>
                <span className={`tier-badge tier-${user.customer_tier}`}>
                  {user.customer_tier}
                </span>
              </div>
              <div className="info-item full-width">
                <span className="info-label">Address 1:</span>
                <span className="info-value">{user.address1 || 'N/A'}</span>
              </div>
              <div className="info-item full-width">
                <span className="info-label">Address 2:</span>
                <span className="info-value">{user.address2 || 'N/A'}</span>
              </div>
              <div className="info-item">
                <span className="info-label">City:</span>
                <span className="info-value">{user.city || 'N/A'}</span>
              </div>
              <div className="info-item">
                <span className="info-label">State:</span>
                <span className="info-value">{user.state || 'N/A'}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Zip Code:</span>
                <span className="info-value">{user.zipcode || 'N/A'}</span>
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
                <span className="info-label">Last Interaction:</span>
                <span className="info-value">
                  {formatToCST(user.last_interaction)}
                </span>
              </div>
              <div className="info-item full-width">
                <span className="info-label">Created:</span>
                <span className="info-value">
                  {formatToCST(user.created_at)}
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
            </div>
            
            <div className="form-group">
              <label htmlFor="address1">Address Line 1</label>
              <input
                type="text"
                id="address1"
                name="address1"
                value={formData.address1}
                onChange={handleInputChange}
                placeholder="123 Main Street"
                disabled={loading}
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="address2">Address Line 2</label>
              <input
                type="text"
                id="address2"
                name="address2"
                value={formData.address2}
                onChange={handleInputChange}
                placeholder="Apt 4B (Optional)"
                disabled={loading}
              />
            </div>
            
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="city">City</label>
                <input
                  type="text"
                  id="city"
                  name="city"
                  value={formData.city}
                  onChange={handleInputChange}
                  placeholder="New York"
                  disabled={loading}
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="state">State</label>
                <input
                  type="text"
                  id="state"
                  name="state"
                  value={formData.state}
                  onChange={handleInputChange}
                  placeholder="NY"
                  disabled={loading}
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="zipcode">Zip Code</label>
                <input
                  type="text"
                  id="zipcode"
                  name="zipcode"
                  value={formData.zipcode}
                  onChange={handleInputChange}
                  placeholder="10001"
                  disabled={loading}
                />
              </div>
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
                    handleInputChange({
                      target: {
                        name: 'subscription',
                        value: e.target.checked ? 'subscribed' : 'unsubscribed'
                      }
                    });
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

export default UpdateUserFormView;
