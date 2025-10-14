import React from 'react';

function AddUserFormView({
  formData,
  tagInput,
  setTagInput,
  alert,
  loading,
  handleInputChange,
  handleAddTag,
  handleRemoveTag,
  handleSubmit,
  resetForm
}) {
  return (
    <div className="add-user-container">
      <div className="form-card">
        <div className="form-header">
          <h1>📱 Add New User</h1>
          <p className="subtitle">Manually add a customer to the WhatsApp Business database</p>
        </div>
        
        {alert && (
          <div className={`alert alert-${alert.type}`}>
            {alert.message}
          </div>
        )}
        
        <form onSubmit={handleSubmit} className="user-form">
          <div className="form-group">
            <label htmlFor="whatsapp_phone">
              WhatsApp Phone Number <span className="required">*</span>
            </label>
            <input
              type="tel"
              id="whatsapp_phone"
              name="whatsapp_phone"
              value={formData.whatsapp_phone}
              onChange={handleInputChange}
              placeholder="+1234567890"
              required
              pattern="^\+?[1-9]\d{1,14}$"
              title="Enter phone with country code (e.g., +1234567890)"
              disabled={loading}
            />
            <small className="help-text">Include country code (e.g., +1 for US)</small>
          </div>
          
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
          
          <div className="form-row">
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
                      aria-label="Remove tag"
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
              placeholder="Additional notes about this customer..."
              rows="4"
              disabled={loading}
            />
          </div>
          
          <div className="button-group">
            <button 
              type="submit" 
              className="btn btn-primary"
              disabled={loading}
            >
              {loading ? '⏳ Adding User...' : '✅ Add User'}
            </button>
            <button 
              type="button" 
              className="btn btn-secondary"
              onClick={resetForm}
              disabled={loading}
            >
              🔄 Reset
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default AddUserFormView;
