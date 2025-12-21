import React, { useState } from 'react';
import './UpdateUserForm.css';
import UpdateUserFormView from './UpdateUserFormView';
import config from '../config';

function UpdateUserForm() {
  const [searchPhone, setSearchPhone] = useState('');
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searching, setSearching] = useState(false);
  const [alert, setAlert] = useState(null);
  const [tagInput, setTagInput] = useState('');
  
  const [formData, setFormData] = useState({
    display_name: '',
    address1: '',
    address2: '',
    city: '',
    state: '',
    zipcode: '',
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
        `${config.API_URL}/api/users/${encodeURIComponent(searchPhone.trim())}`
      );

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        
        // Populate form with user data (map backend field names to frontend)
        setFormData({
          display_name: userData.display_name || '',
          address1: userData.address_line1 || '',
          address2: userData.address_line2 || '',
          city: userData.city || '',
          state: userData.state || '',
          zipcode: userData.zipcode || '',
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

    // Prepare update data (map frontend field names to backend field names)
    const updateData = {
      display_name: formData.display_name.trim() || null,
      address_line1: formData.address1.trim() || null,
      address_line2: formData.address2.trim() || null,
      city: formData.city.trim() || null,
      state: formData.state.trim() || null,
      zipcode: formData.zipcode.trim() || null,
      email: formData.email.trim() || null,
      customer_tier: formData.customer_tier,
      tags: formData.tags,
      notes: formData.notes.trim() || null,
      subscription: formData.subscription
    };

    try {
      const response = await fetch(
        `${config.API_URL}/api/users/${encodeURIComponent(user.whatsapp_phone)}`,
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
        
        // Refresh form with updated data (map backend field names to frontend)
        setFormData({
          display_name: result.display_name || '',
          address1: result.address_line1 || '',
          address2: result.address_line2 || '',
          city: result.city || '',
          state: result.state || '',
          zipcode: result.zipcode || '',
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
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
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
    if (user) {
      setFormData({
        display_name: user.display_name || '',
        address1: user.address_line1 || '',
        address2: user.address_line2 || '',
        city: user.city || '',
        state: user.state || '',
        zipcode: user.zipcode || '',
        email: user.email || '',
        customer_tier: user.customer_tier || 'regular',
        tags: user.tags || [],
        notes: user.notes || '',
        subscription: user.subscription || 'subscribed'
      });
      setTagInput('');
      setAlert({ type: 'info', message: 'ℹ️ Form reset to current user data' });
    }
  };

  return (
    <UpdateUserFormView
      searchPhone={searchPhone}
      setSearchPhone={setSearchPhone}
      user={user}
      searching={searching}
      alert={alert}
      formData={formData}
      tagInput={tagInput}
      setTagInput={setTagInput}
      loading={loading}
      handleSearch={handleSearch}
      handleUpdate={handleUpdate}
      handleInputChange={handleInputChange}
      handleAddTag={handleAddTag}
      handleRemoveTag={handleRemoveTag}
      handleReset={handleReset}
    />
  );
}

export default UpdateUserForm;
