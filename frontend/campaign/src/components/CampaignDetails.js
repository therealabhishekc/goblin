/**
 * Campaign Details Component
 * Shows detailed stats and allows campaign management
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { campaignAPI } from '../services/api';
import {
  formatDateTime,
  formatNumber,
  formatPercentage,
  getStatusText,
  formatDate,
} from '../utils/formatters';

function CampaignDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    loadStats();
    // Auto-refresh every 10 seconds if campaign is active
    const interval = setInterval(() => {
      if (stats?.status === 'active') {
        loadStats();
      }
    }, 10000);
    return () => clearInterval(interval);
  }, [id]);

  const loadStats = async () => {
    try {
      setError(null);
      const data = await campaignAPI.getCampaignStats(id);
      setStats(data);
      setLoading(false);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load campaign stats');
      setLoading(false);
    }
  };

  const handlePause = async () => {
    if (!window.confirm('Pause this campaign? No more messages will be sent until resumed.')) {
      return;
    }
    setActionLoading(true);
    try {
      await campaignAPI.pauseCampaign(id);
      alert('✅ Campaign paused');
      loadStats();
    } catch (err) {
      alert(`❌ Error: ${err.response?.data?.detail || 'Failed to pause campaign'}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleResume = async () => {
    if (!window.confirm('Resume this campaign? Scheduled messages will start sending again.')) {
      return;
    }
    setActionLoading(true);
    try {
      await campaignAPI.resumeCampaign(id);
      alert('✅ Campaign resumed');
      loadStats();
    } catch (err) {
      alert(`❌ Error: ${err.response?.data?.detail || 'Failed to resume campaign'}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleCancel = async () => {
    if (!window.confirm('⚠️ Cancel this campaign?\n\nThis action CANNOT be undone.\nPending messages will NOT be sent.')) {
      return;
    }
    setActionLoading(true);
    try {
      await campaignAPI.cancelCampaign(id);
      alert('✅ Campaign cancelled');
      loadStats();
    } catch (err) {
      alert(`❌ Error: ${err.response?.data?.detail || 'Failed to cancel campaign'}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleActivate = async () => {
    if (!window.confirm('Activate this campaign and start sending messages?')) {
      return;
    }
    setActionLoading(true);
    try {
      await campaignAPI.activateCampaign(id);
      alert('✅ Campaign activated');
      loadStats();
    } catch (err) {
      alert(`❌ Error: ${err.response?.data?.detail || 'Failed to activate campaign'}`);
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="card">
        <div className="alert alert-error">{error || 'Campaign not found'}</div>
        <button className="btn btn-secondary" onClick={() => navigate('/')}>
          ← Back to Campaigns
        </button>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="card">
        <div className="card-header">
          <div>
            <button className="btn btn-secondary btn-small" onClick={() => navigate('/')}>
              ← Back
            </button>
            <h2 className="card-title" style={{ marginTop: '1rem' }}>
              {stats.campaign_name}
            </h2>
            <span className={`status-badge status-${stats.status}`}>
              {getStatusText(stats.status)}
            </span>
          </div>
          
          {/* Action Buttons */}
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            {stats.status === 'draft' && (
              <button
                className="btn btn-success btn-small"
                onClick={handleActivate}
                disabled={actionLoading}
              >
                🚀 Activate
              </button>
            )}
            {stats.status === 'active' && (
              <button
                className="btn btn-warning btn-small"
                onClick={handlePause}
                disabled={actionLoading}
              >
                ⏸️ Pause
              </button>
            )}
            {stats.status === 'paused' && (
              <>
                <button
                  className="btn btn-success btn-small"
                  onClick={handleResume}
                  disabled={actionLoading}
                >
                  ▶️ Resume
                </button>
                <button
                  className="btn btn-danger btn-small"
                  onClick={handleCancel}
                  disabled={actionLoading}
                >
                  ✕ Cancel
                </button>
              </>
            )}
            {(stats.status === 'active' || stats.status === 'draft') && (
              <button
                className="btn btn-danger btn-small"
                onClick={handleCancel}
                disabled={actionLoading}
              >
                ✕ Cancel
              </button>
            )}
          </div>
        </div>

        {/* Progress Bar */}
        <div style={{ marginBottom: '2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
            <span style={{ fontWeight: '500' }}>Campaign Progress</span>
            <span style={{ fontWeight: '600', color: '#667eea' }}>
              {stats.progress_percentage}%
            </span>
          </div>
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${stats.progress_percentage}%` }}
            >
              {stats.progress_percentage > 5 && `${stats.progress_percentage}%`}
            </div>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.5rem', fontSize: '0.9rem', color: '#6c757d' }}>
            <span>{formatNumber(stats.sent)} sent</span>
            <span>{formatNumber(stats.total_target)} total</span>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-label">Total Recipients</div>
            <div className="stat-value">{formatNumber(stats.total_target)}</div>
          </div>

          <div className="stat-card" style={{ borderLeftColor: '#28a745' }}>
            <div className="stat-label">Messages Sent</div>
            <div className="stat-value">{formatNumber(stats.sent)}</div>
          </div>

          <div className="stat-card" style={{ borderLeftColor: '#17a2b8' }}>
            <div className="stat-label">Delivered</div>
            <div className="stat-value">{formatNumber(stats.delivered)}</div>
            <div className="stat-subvalue">
              {stats.delivery_rate ? formatPercentage(stats.delivery_rate) : 'N/A'}
            </div>
          </div>

          <div className="stat-card" style={{ borderLeftColor: '#6f42c1' }}>
            <div className="stat-label">Read</div>
            <div className="stat-value">{formatNumber(stats.read)}</div>
            <div className="stat-subvalue">
              {stats.read_rate ? formatPercentage(stats.read_rate) : 'N/A'}
            </div>
          </div>

          <div className="stat-card" style={{ borderLeftColor: '#dc3545' }}>
            <div className="stat-label">Failed</div>
            <div className="stat-value">{formatNumber(stats.failed)}</div>
          </div>

          <div className="stat-card" style={{ borderLeftColor: '#ffc107' }}>
            <div className="stat-label">Pending</div>
            <div className="stat-value">{formatNumber(stats.pending)}</div>
          </div>
        </div>

        {/* Additional Info */}
        {stats.estimated_completion_date && (
          <div className="alert alert-info">
            <strong>📅 Estimated Completion:</strong> {formatDate(stats.estimated_completion_date)}
            <br />
            <small style={{ color: '#0c5460' }}>
              Based on current daily send limit and pending messages
            </small>
          </div>
        )}

        {/* Campaign Details */}
        <div style={{ marginTop: '2rem', padding: '1.5rem', background: '#f8f9fa', borderRadius: '8px' }}>
          <h3 style={{ marginBottom: '1rem', fontSize: '1.2rem' }}>Campaign Information</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem' }}>
            <div>
              <strong>Campaign ID:</strong><br />
              <code style={{ fontSize: '0.85rem', background: 'white', padding: '0.25rem 0.5rem', borderRadius: '3px' }}>
                {stats.campaign_id}
              </code>
            </div>
            <div>
              <strong>Status:</strong><br />
              <span className={`status-badge status-${stats.status}`}>
                {getStatusText(stats.status)}
              </span>
            </div>
          </div>
        </div>

        {/* Performance Metrics */}
        {(stats.delivery_rate || stats.read_rate) && (
          <div style={{ marginTop: '2rem' }}>
            <h3 style={{ marginBottom: '1rem', fontSize: '1.2rem' }}>Performance Metrics</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
              {stats.delivery_rate && (
                <div style={{ padding: '1rem', background: '#d4edda', borderRadius: '8px' }}>
                  <div style={{ fontSize: '0.85rem', color: '#155724', marginBottom: '0.5rem' }}>
                    DELIVERY RATE
                  </div>
                  <div style={{ fontSize: '2rem', fontWeight: '700', color: '#155724' }}>
                    {formatPercentage(stats.delivery_rate)}
                  </div>
                </div>
              )}
              {stats.read_rate && (
                <div style={{ padding: '1rem', background: '#d1ecf1', borderRadius: '8px' }}>
                  <div style={{ fontSize: '0.85rem', color: '#0c5460', marginBottom: '0.5rem' }}>
                    READ RATE
                  </div>
                  <div style={{ fontSize: '2rem', fontWeight: '700', color: '#0c5460' }}>
                    {formatPercentage(stats.read_rate)}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Refresh Info */}
        {stats.status === 'active' && (
          <div style={{ marginTop: '2rem', textAlign: 'center', color: '#6c757d', fontSize: '0.9rem' }}>
            🔄 Auto-refreshing every 10 seconds
          </div>
        )}
      </div>
    </div>
  );
}

export default CampaignDetails;
