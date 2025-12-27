import React from 'react';
import { motion } from 'framer-motion';
import { 
  FiHome, FiMessageSquare, FiUsers, FiBarChart2, 
  FiSettings, FiTarget, FiArchive, FiLogOut 
} from 'react-icons/fi';
import { useNavigate, useLocation } from 'react-router-dom';
import './Layout.css';

const Layout = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    { icon: FiHome, label: 'Dashboard', path: '/dashboard' },
    { icon: FiMessageSquare, label: 'Messages', path: '/messages' },
    { icon: FiTarget, label: 'Campaigns', path: '/campaigns' },
    { icon: FiUsers, label: 'Users', path: '/users' },
    { icon: FiSettings, label: 'Settings', path: '/settings' },
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <div className="layout">
      <div className="animated-bg" />
      
      {/* Top Navbar */}
      <header className="navbar">
        <div className="navbar-brand">
          <h2 className="text-gradient">WhatsApp CRM</h2>
        </div>

        <nav className="navbar-menu">
          {menuItems.map((item) => (
            <motion.button
              key={item.path}
              className={`nav-item glass-button ${isActive(item.path) ? 'active' : ''}`}
              onClick={() => navigate(item.path)}
              whileHover={{ scale: 1.15 }}
              whileTap={{ scale: 0.95 }}
            >
              <item.icon className="nav-icon" />
              <span className="nav-label">{item.label}</span>
            </motion.button>
          ))}
        </nav>

        <div className="navbar-actions">
          <button className="glass-button">Profile</button>
          <button className="glass-button glass-button-primary">
            <FiLogOut /> Logout
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content">
        <div className="content-area">
          {children}
        </div>
      </main>
    </div>
  );
};

export default Layout;