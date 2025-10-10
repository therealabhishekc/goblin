import React, { useState } from 'react';
import './AddUserForm.css';

function AddUserForm() {
  const [formData, setFormData] = useState({
    whatsapp_phone: '',
    display_name: '',
    business_name: '',
    email: '',
    customer_tier: 'regular',
    tags: [],
    notes: ''
  });
  
  const [tagInput, setTagInput] = useState('');
  const [alert, setAlert] = useState(null);
  const [loading, setLoading] = useState(false);
  
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
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
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setAlert(null);
    
    // Validate phone number
    if (!formData.whatsapp_phone.trim()) {
      setAlert({ type: 'error', message: '❌ Phone number is required!' });
      setLoading(false);
      return;
    }
    
    // Prepare data - remove empty fields
    const submitData = {
      whatsapp_phone: formData.whatsapp_phone.trim(),
      display_name: formData.display_name.trim() || null,
      business_name: formData.business_name.trim() || null,
      email: formData.email.trim() || null,
      customer_tier: formData.customer_tier,
      tags: formData.tags,
      notes: formData.notes.trim() || null
    };
    
    try {
      const response = await fetch('https://hwwsxxpemc.us-east-1.awsapprunner.com/api/users', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(submitData)
      });
      
      const result = await response.json();
      
      if (response.ok) {
        setAlert({ 
          type: 'success', 
          message: `✅ User "${submitData.whatsapp_phone}" added successfully!` 
        });
        // Reset form after successful submission
        setTimeout(() => {
          resetForm();
        }, 2000);
      } else {
        setAlert({ 
          type: 'error', 
          message: `❌ Error: ${result.detail || 'Failed to add user'}` 
        });
      }
    } catch (error) {
      setAlert({ 
        type: 'error', 
        message: `❌ Network Error: ${error.message}. Make sure the backend is running` 
      });
    } finally {
      setLoading(false);
    }
  };
  
  const resetForm = () => {
    setFormData({
      whatsapp_phone: '',
      display_name: '',
      business_name: '',
      email: '',
      customer_tier: 'regular',
      tags: [],
      notes: ''
    });
    setTagInput('');
    setAlert(null);
  };
  
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

export default AddUserForm;
