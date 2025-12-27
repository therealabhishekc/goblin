import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  FiMoon, FiSun, FiBell, FiGlobe, FiLock, 
  FiUser, FiMail, FiPhone, FiSave 
} from 'react-icons/fi';
import { useTheme } from '../contexts/ThemeContext';
import './Settings.css';

const Settings = () => {
  const { isDarkMode, toggleTheme } = useTheme();
  const [settings, setSettings] = useState({
    email: '',
    phone: '',
    notifications: true,
    language: 'en',
  });

  const handleSave = () => {
    // Save settings to backend
    console.log('Saving settings:', settings);
  };

  return (
    <div className="settings">
      <div className="settings-header">
        <h1 className="text-gradient">Settings</h1>
        <p className="settings-subtitle">Manage your preferences and account settings</p>
      </div>

      <div className="settings-content">
        {/* Appearance Section */}
        <motion.div
          className="settings-section glass-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          whileHover={{ y: -2 }}
        >
          <h2>
            <FiSun /> Appearance
          </h2>
          
          <div className="setting-item">
            <div className="setting-info">
              <div className="setting-icon">
                {isDarkMode ? <FiMoon /> : <FiSun />}
              </div>
              <div>
                <h3>Dark Mode</h3>
                <p>Toggle between light and dark theme</p>
              </div>
            </div>
            <label className="toggle-switch">
              <input
                type="checkbox"
                checked={isDarkMode}
                onChange={toggleTheme}
              />
              <span className="toggle-slider"></span>
            </label>
          </div>
        </motion.div>

        {/* Notifications Section */}
        <motion.div
          className="settings-section glass-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          whileHover={{ y: -2 }}
        >
          <h2>
            <FiBell /> Notifications
          </h2>
          
          <div className="setting-item">
            <div className="setting-info">
              <div className="setting-icon">
                <FiBell />
              </div>
              <div>
                <h3>Push Notifications</h3>
                <p>Receive notifications about messages and campaigns</p>
              </div>
            </div>
            <label className="toggle-switch">
              <input
                type="checkbox"
                checked={settings.notifications}
                onChange={(e) => setSettings({ ...settings, notifications: e.target.checked })}
              />
              <span className="toggle-slider"></span>
            </label>
          </div>
        </motion.div>

        {/* Account Section */}
        <motion.div
          className="settings-section glass-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          whileHover={{ y: -2 }}
        >
          <h2>
            <FiUser /> Account
          </h2>
          
          <div className="setting-form">
            <div className="form-group">
              <label>
                <FiMail /> Email Address
              </label>
              <input
                type="email"
                className="glass-input"
                placeholder="your.email@example.com"
                value={settings.email}
                onChange={(e) => setSettings({ ...settings, email: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label>
                <FiPhone /> Phone Number
              </label>
              <input
                type="tel"
                className="glass-input"
                placeholder="+1 (555) 123-4567"
                value={settings.phone}
                onChange={(e) => setSettings({ ...settings, phone: e.target.value })}
              />
            </div>
          </div>
        </motion.div>

        {/* Language Section */}
        <motion.div
          className="settings-section glass-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          whileHover={{ y: -2 }}
        >
          <h2>
            <FiGlobe /> Language & Region
          </h2>
          
          <div className="form-group">
            <label>
              <FiGlobe /> Language
            </label>
            <select
              className="glass-input"
              value={settings.language}
              onChange={(e) => setSettings({ ...settings, language: e.target.value })}
            >
              <option value="en">English</option>
              <option value="es">Español</option>
              <option value="fr">Français</option>
              <option value="de">Deutsch</option>
              <option value="pt">Português</option>
            </select>
          </div>
        </motion.div>

        {/* Security Section */}
        <motion.div
          className="settings-section glass-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          whileHover={{ y: -2 }}
        >
          <h2>
            <FiLock /> Security
          </h2>
          
          <div className="security-actions">
            <button className="glass-button">
              <FiLock /> Change Password
            </button>
            <button className="glass-button">
              <FiLock /> Two-Factor Authentication
            </button>
          </div>
        </motion.div>

        {/* Save Button */}
        <motion.div
          className="settings-actions"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
        >
          <button className="glass-button glass-button-primary" onClick={handleSave}>
            <FiSave /> Save Changes
          </button>
        </motion.div>
      </div>
    </div>
  );
};

export default Settings;
