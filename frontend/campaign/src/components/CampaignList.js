/**
 * Campaign List Component
 * Displays all campaigns with filtering and status overview
 */
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { campaignAPI } from '../services/api';
import {
  formatDate,
  formatNumber,
  getStatusText,
  calculateProgress,
} from '../utils/formatters';

function CampaignList() {
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusFilter, setStatusFilter] = useState('all');
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    loadCampaigns();
  }, [statusFilter]);

  const loadCampaigns = async () => {
    try {
      setLoading(true);
      setError(null);
      const filter = statusFilter === 'all' ? null : statusFilter;
      const data = await campaignAPI.listCampaigns(filter);
      setCampaigns(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load campaigns');
    } finally {
      setLoading(false);
    }
  };

  const handleProcessDaily = async () => {
    if (!window.confirm('Process today\'s campaigns and send scheduled messages?')) {
      return;
    }

    try {
      setProcessing(true);
      const result = await campaignAPI.processDailyCampaigns();
      alert(`✅ Success!\n\nCampaigns processed: ${result.campaigns_processed}\nMessages sent: ${result.messages_sent}`);
      loadCampaigns(); // Reload to show updated stats
    } catch (err) {
      alert(`❌ Error: ${err.response?.data?.detail || 'Failed to process campaigns'}`);
    } finally {
      setProcessing(false);
    }
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Marketing Campaigns</h2>
          <div style={{ display: 'flex', gap: '1rem' }}>
            <button
              className="btn btn-warning btn-small"
              onClick={handleProcessDaily}
              disabled={processing}
            >
              {processing ? 'Processing...' : '🚀 Process Daily'}
            </button>
            <Link to="/create" className="btn btn-primary btn-small">
              ➕ Create Campaign
            </Link>
          </div>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        {/* Status Filter */}
        <div style={{ marginBottom: '1.5rem' }}>
          <label className="form-label">Filter by Status:</label>
          <select
            className="form-select"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{ maxWidth: '200px' }}
          >
            <option value="all">All Campaigns</option>
            <option value="draft">Draft</option>
            <option value="active">Active</option>
            <option value="paused">Paused</option>
            <option value="completed">Completed</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>

        {/* Campaigns List */}
        {campaigns.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#6c757d' }}>
            <p style={{ fontSize: '1.2rem' }}>No campaigns found</p>
            <Link to="/create" className="btn btn-primary" style={{ marginTop: '1rem' }}>
              Create Your First Campaign
            </Link>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="table">
              <thead>
                <tr>
                  <th>Campaign Name</th>
                  <th>Status</th>
                  <th>Template</th>
                  <th>Progress</th>
                  <th>Sent</th>
                  <th>Pending</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {campaigns.map((campaign) => (
                  <tr key={campaign.id}>
                    <td>
                      <strong>{campaign.name}</strong>
                    </td>
                    <td>
                      <span className={`status-badge status-${campaign.status}`}>
                        {getStatusText(campaign.status)}
                      </span>
                    </td>
                    <td>{campaign.template_name}</td>
                    <td style={{ minWidth: '150px' }}>
                      <div className="progress-bar">
                        <div
                          className="progress-fill"
                          style={{ width: `${campaign.progress}%` }}
                        >
                          {campaign.progress > 10 && `${campaign.progress}%`}
                        </div>
                      </div>
                      <small style={{ color: '#6c757d' }}>
                        {campaign.progress}% complete
                      </small>
                    </td>
                    <td>{formatNumber(campaign.messages_sent)}</td>
                    <td>{formatNumber(campaign.messages_pending)}</td>
                    <td>{formatDate(campaign.created_at)}</td>
                    <td>
                      <Link
                        to={`/campaign/${campaign.id}`}
                        className="btn btn-secondary btn-small"
                      >
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default CampaignList;
