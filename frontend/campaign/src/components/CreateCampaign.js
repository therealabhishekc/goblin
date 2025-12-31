/**
 * Create Campaign Component
 * Multi-step form for creating new campaigns
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { campaignAPI } from '../services/api';

function CreateCampaign() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Form data
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    template_name: '',
    language_code: 'en_US',
    daily_send_limit: 250,
    priority: 5,
    target_audience: {
      customer_tier: 'all',  // Default to "all" tiers
      city: '',
      state: '',
      tags: '',
    },
  });

  const [recipientData, setRecipientData] = useState({
    use_target_audience: true,
    phone_numbers: '',
  });

  const [activationData, setActivationData] = useState({
    start_date: '',
  });

  const [createdCampaignId, setCreatedCampaignId] = useState(null);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleAudienceChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      target_audience: {
        ...prev.target_audience,
        [name]: value,
      },
    }));
  };

  // Step 1: Create Campaign
  const handleCreateCampaign = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Prepare target audience
      const targetAudience = {};
      // Always include customer_tier, default to "all" if not specified
      targetAudience.customer_tier = formData.target_audience.customer_tier || "all";
      
      if (formData.target_audience.city) {
        targetAudience.city = formData.target_audience.city;
      }
      if (formData.target_audience.state) {
        targetAudience.state = formData.target_audience.state;
      }
      if (formData.target_audience.tags) {
        targetAudience.tags = formData.target_audience.tags.split(',').map(t => t.trim());
      }

      const campaignData = {
        name: formData.name,
        description: formData.description,
        template_name: formData.template_name,
        language_code: formData.language_code,
        daily_send_limit: parseInt(formData.daily_send_limit),
        priority: parseInt(formData.priority),
        target_audience: Object.keys(targetAudience).length > 0 ? targetAudience : null,
      };

      const result = await campaignAPI.createCampaign(campaignData);
      setCreatedCampaignId(result.id);
      setStep(2);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create campaign');
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Add Recipients
  const handleAddRecipients = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (recipientData.use_target_audience) {
        await campaignAPI.addRecipientsFromAudience(createdCampaignId);
      } else {
        const phoneNumbers = recipientData.phone_numbers
          .split('\n')
          .map(p => p.trim())
          .filter(p => p.length > 0);
        
        await campaignAPI.addRecipients(createdCampaignId, { phone_numbers: phoneNumbers });
      }
      setStep(3);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to add recipients');
    } finally {
      setLoading(false);
    }
  };

  // Step 3: Activate Campaign
  const handleActivate = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await campaignAPI.activateCampaign(
        createdCampaignId,
        activationData.start_date || null
      );
      alert('✅ Campaign activated successfully!');
      navigate(`/campaign/${createdCampaignId}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to activate campaign');
    } finally {
      setLoading(false);
    }
  };

  const handleSkipActivation = () => {
    navigate(`/campaign/${createdCampaignId}`);
  };

  return (
    <div className="card">
      <div className="card-header">
        <h2 className="card-title">Create New Campaign</h2>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {/* Step Indicator */}
      <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '50%',
            background: step >= 1 ? '#667eea' : '#e9ecef',
            color: 'white',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 'bold',
          }}>
            1
          </div>
          <div style={{ width: '50px', height: '2px', background: step >= 2 ? '#667eea' : '#e9ecef' }}></div>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '50%',
            background: step >= 2 ? '#667eea' : '#e9ecef',
            color: step >= 2 ? 'white' : '#6c757d',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 'bold',
          }}>
            2
          </div>
          <div style={{ width: '50px', height: '2px', background: step >= 3 ? '#667eea' : '#e9ecef' }}></div>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '50%',
            background: step >= 3 ? '#667eea' : '#e9ecef',
            color: step >= 3 ? 'white' : '#6c757d',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 'bold',
          }}>
            3
          </div>
        </div>
      </div>

      {/* Step 1: Campaign Details */}
      {step === 1 && (
        <form onSubmit={handleCreateCampaign}>
          <h3 style={{ marginBottom: '1.5rem' }}>Step 1: Campaign Details</h3>
          
          <div className="form-group">
            <label className="form-label">Campaign Name *</label>
            <input
              type="text"
              name="name"
              className="form-input"
              value={formData.name}
              onChange={handleInputChange}
              required
              placeholder="e.g., Summer Sale 2025"
            />
          </div>

          <div className="form-group">
            <label className="form-label">Description</label>
            <textarea
              name="description"
              className="form-textarea"
              value={formData.description}
              onChange={handleInputChange}
              placeholder="Brief description of the campaign..."
            />
          </div>

          <div className="form-group">
            <label className="form-label">WhatsApp Template Name *</label>
            <input
              type="text"
              name="template_name"
              className="form-input"
              value={formData.template_name}
              onChange={handleInputChange}
              required
              placeholder="e.g., summer_sale_promo"
            />
            <small className="form-help">Must be an approved WhatsApp template</small>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label className="form-label">Language Code</label>
              <select
                name="language_code"
                className="form-select"
                value={formData.language_code}
                onChange={handleInputChange}
              >
                <option value="en_US">English (US)</option>
                <option value="es_ES">Spanish (Spain)</option>
                <option value="es_MX">Spanish (Mexico)</option>
                <option value="fr_FR">French</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Daily Send Limit</label>
              <input
                type="number"
                name="daily_send_limit"
                className="form-input"
                value={formData.daily_send_limit}
                onChange={handleInputChange}
                min="1"
                max="250"
              />
              <small className="form-help">Max 250 per day (WhatsApp limit)</small>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Priority (1-10)</label>
            <input
              type="number"
              name="priority"
              className="form-input"
              value={formData.priority}
              onChange={handleInputChange}
              min="1"
              max="10"
            />
            <small className="form-help">1 = highest priority, 10 = lowest</small>
          </div>

          <h4 style={{ marginTop: '2rem', marginBottom: '1rem' }}>Target Audience (Optional)</h4>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label className="form-label">Customer Tier</label>
              <select
                name="customer_tier"
                className="form-select"
                value={formData.target_audience.customer_tier}
                onChange={handleAudienceChange}
              >
                <option value="all">All Tiers</option>
                <option value="regular">Regular</option>
                <option value="premium">Premium</option>
                <option value="vip">VIP</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">City</label>
              <input
                type="text"
                name="city"
                className="form-input"
                value={formData.target_audience.city}
                onChange={handleAudienceChange}
                placeholder="e.g., New York"
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label className="form-label">State</label>
              <input
                type="text"
                name="state"
                className="form-input"
                value={formData.target_audience.state}
                onChange={handleAudienceChange}
                placeholder="e.g., NY"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Tags</label>
              <input
                type="text"
                name="tags"
                className="form-input"
                value={formData.target_audience.tags}
                onChange={handleAudienceChange}
                placeholder="e.g., fashion, accessories"
              />
              <small className="form-help">Comma-separated tags</small>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
            <button type="button" className="btn btn-secondary" onClick={() => navigate('/')}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Creating...' : 'Next: Add Recipients →'}
            </button>
          </div>
        </form>
      )}

      {/* Step 2: Add Recipients */}
      {step === 2 && (
        <form onSubmit={handleAddRecipients}>
          <h3 style={{ marginBottom: '1.5rem' }}>Step 2: Add Recipients</h3>

          <div className="form-group">
            <label className="form-label">Recipient Selection Method</label>
            <div style={{ display: 'flex', gap: '2rem', marginTop: '0.5rem' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <input
                  type="radio"
                  checked={recipientData.use_target_audience}
                  onChange={() => setRecipientData({ ...recipientData, use_target_audience: true })}
                />
                <span>Auto-select from target audience</span>
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <input
                  type="radio"
                  checked={!recipientData.use_target_audience}
                  onChange={() => setRecipientData({ ...recipientData, use_target_audience: false })}
                />
                <span>Manual phone numbers</span>
              </label>
            </div>
          </div>

          {recipientData.use_target_audience ? (
            <div className="alert alert-info">
              <strong>Auto-selection:</strong> All subscribed customers matching your target audience will be automatically added.
            </div>
          ) : (
            <div className="form-group">
              <label className="form-label">Phone Numbers *</label>
              <textarea
                className="form-textarea"
                value={recipientData.phone_numbers}
                onChange={(e) => setRecipientData({ ...recipientData, phone_numbers: e.target.value })}
                placeholder="Enter phone numbers, one per line&#10;14694652751&#10;19453083188&#10;15551234567"
                rows="10"
                required={!recipientData.use_target_audience}
                style={{ fontFamily: 'monospace' }}
              />
              <small className="form-help">One phone number per line (include country code)</small>
            </div>
          )}

          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
            <button type="button" className="btn btn-secondary" onClick={() => setStep(1)}>
              ← Back
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Adding...' : 'Next: Activate Campaign →'}
            </button>
          </div>
        </form>
      )}

      {/* Step 3: Activate Campaign */}
      {step === 3 && (
        <form onSubmit={handleActivate}>
          <h3 style={{ marginBottom: '1.5rem' }}>Step 3: Activate Campaign</h3>

          <div className="alert alert-success">
            <strong>✅ Recipients added successfully!</strong><br />
            Ready to activate and schedule the campaign.
          </div>

          <div className="form-group">
            <label className="form-label">Start Date (Optional)</label>
            <input
              type="date"
              className="form-input"
              value={activationData.start_date}
              onChange={(e) => setActivationData({ start_date: e.target.value })}
              min={new Date().toISOString().split('T')[0]}
              style={{ maxWidth: '300px' }}
            />
            <small className="form-help">Leave empty to start tomorrow</small>
          </div>

          <div className="alert alert-info">
            <strong>ℹ️ What happens when you activate:</strong>
            <ul style={{ marginTop: '0.5rem', marginLeft: '1.5rem' }}>
              <li>Campaign status changes to "Active"</li>
              <li>Recipients are scheduled across multiple days (250/day max)</li>
              <li>Messages will be sent automatically by the daily processor</li>
              <li>You can pause/resume the campaign anytime</li>
            </ul>
          </div>

          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
            <button type="button" className="btn btn-secondary" onClick={handleSkipActivation}>
              Skip (Activate Later)
            </button>
            <button type="submit" className="btn btn-success" disabled={loading}>
              {loading ? 'Activating...' : '🚀 Activate Campaign'}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}

export default CreateCampaign;
