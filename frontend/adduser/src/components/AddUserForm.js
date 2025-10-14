import React, { useState } from 'react';
import './AddUserForm.css';
import AddUserFormView from './AddUserFormView';

function AddUserForm() {
  const [formData, setFormData] = useState({
    whatsapp_phone: '',
    display_name: '',
    address1: '',
    address2: '',
    city: '',
    state: '',
    zipcode: '',
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
      address1: formData.address1.trim() || null,
      address2: formData.address2.trim() || null,
      city: formData.city.trim() || null,
      state: formData.state.trim() || null,
      zipcode: formData.zipcode.trim() || null,
      email: formData.email.trim() || null,
      customer_tier: formData.customer_tier,
      tags: formData.tags,
      notes: formData.notes.trim() || null
    };
    
    try {
      const response = await fetch('https://2mm6fm7ffm.us-east-1.awsapprunner.com/api/users', {
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
      address1: '',
      address2: '',
      city: '',
      state: '',
      zipcode: '',
      email: '',
      customer_tier: 'regular',
      tags: [],
      notes: ''
    });
    setTagInput('');
    setAlert(null);
  };
  
  return (
    <AddUserFormView
      formData={formData}
      tagInput={tagInput}
      setTagInput={setTagInput}
      alert={alert}
      loading={loading}
      handleInputChange={handleInputChange}
      handleAddTag={handleAddTag}
      handleRemoveTag={handleRemoveTag}
      handleSubmit={handleSubmit}
      resetForm={resetForm}
    />
  );
}

export default AddUserForm;
