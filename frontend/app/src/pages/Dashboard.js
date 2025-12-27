import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { 
  FiMessageSquare, FiUsers, FiTrendingUp, FiTarget,
  FiCheck, FiClock, FiAlertCircle 
} from 'react-icons/fi';
import { apiService } from '../services/api';
import './Dashboard.css';

const Dashboard = () => {
  const [stats, setStats] = useState({
    totalMessages: 0,
    totalUsers: 0,
    activeCampaigns: 0,
    deliveryRate: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const response = await apiService.getDashboardStats();
      setStats(response.data);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const statCards = [
    {
      icon: FiMessageSquare,
      label: 'Total Messages',
      value: stats.totalMessages || '12,345',
      change: '+12.5%',
      color: '#6366f1',
    },
    {
      icon: FiUsers,
      label: 'Active Users',
      value: stats.totalUsers || '2,847',
      change: '+5.2%',
      color: '#8b5cf6',
    },
    {
      icon: FiTarget,
      label: 'Active Campaigns',
      value: stats.activeCampaigns || '8',
      change: '+2',
      color: '#ec4899',
    },
    {
      icon: FiTrendingUp,
      label: 'Delivery Rate',
      value: `${stats.deliveryRate || '98.2'}%`,
      change: '+1.2%',
      color: '#10b981',
    },
  ];

  const recentActivity = [
    { 
      id: 1, 
      type: 'message', 
      text: 'Campaign "Summer Sale" sent to 500 users',
      time: '5 minutes ago',
      icon: FiCheck,
      status: 'success' 
    },
    { 
      id: 2, 
      type: 'campaign', 
      text: 'New campaign "Product Launch" scheduled',
      time: '1 hour ago',
      icon: FiClock,
      status: 'pending' 
    },
    { 
      id: 3, 
      type: 'alert', 
      text: 'Message delivery failed for 3 users',
      time: '2 hours ago',
      icon: FiAlertCircle,
      status: 'error' 
    },
  ];

  if (loading) {
    return (
      <div className="dashboard-loading">
        <motion.div
          className="loading-spinner"
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
        />
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1 className="text-gradient">Dashboard</h1>
        <p className="dashboard-subtitle">Welcome back! Here's your business overview</p>
      </div>

      {/* Stats Grid */}
      <div className="stats-grid">
        {statCards.map((stat, index) => (
          <motion.div
            key={index}
            className="stat-card glass-card"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            whileHover={{ scale: 1.02 }}
          >
            <div className="stat-icon" style={{ color: stat.color }}>
              <stat.icon />
            </div>
            <div className="stat-content">
              <p className="stat-label">{stat.label}</p>
              <h3 className="stat-value">{stat.value}</h3>
              <span className="stat-change positive">{stat.change}</span>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Charts and Activity */}
      <div className="dashboard-content">
        {/* Recent Activity */}
        <motion.div
          className="activity-section glass-card"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4 }}
          whileHover={{ y: -2 }}
        >
          <h2>Recent Activity</h2>
          <div className="activity-list">
            {recentActivity.map((activity) => (
              <motion.div
                key={activity.id}
                className="activity-item"
                whileHover={{ x: 5 }}
              >
                <div className={`activity-icon ${activity.status}`}>
                  <activity.icon />
                </div>
                <div className="activity-content">
                  <p className="activity-text">{activity.text}</p>
                  <span className="activity-time">{activity.time}</span>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Quick Actions */}
        <motion.div
          className="quick-actions glass-card"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.5 }}
          whileHover={{ y: -2 }}
        >
          <h2>Quick Actions</h2>
          <div className="action-buttons">
            <button className="glass-button glass-button-primary">
              <FiMessageSquare /> New Message
            </button>
            <button className="glass-button glass-button-primary">
              <FiTarget /> Create Campaign
            </button>
            <button className="glass-button glass-button-primary">
              <FiUsers /> Add User
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default Dashboard;
