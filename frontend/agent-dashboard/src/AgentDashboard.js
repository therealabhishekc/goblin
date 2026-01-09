import React, { useState, useEffect } from 'react';
import axios from 'axios';
import API_URL from './config';
import './AgentDashboard.css';

const AgentDashboard = () => {
  const [agentId, setAgentId] = useState('');
  const [agentName, setAgentName] = useState('');
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  
  // Tabs
  const [activeTab, setActiveTab] = useState('active'); // 'active', 'all', 'history'
  
  // Sessions
  const [activeSessions, setActiveSessions] = useState([]);
  const [allSessions, setAllSessions] = useState([]);
  const [historySessions, setHistorySessions] = useState([]);
  const [waitingSessions, setWaitingSessions] = useState([]);
  
  // Current chat
  const [selectedSession, setSelectedSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  
  // Search/filter for history
  const [searchTerm, setSearchTerm] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  
  // Auto-refresh
  useEffect(() => {
    if (!isLoggedIn) return;
    
    const interval = setInterval(() => {
      refreshData();
    }, 5000); // Refresh every 5 seconds
    
    return () => clearInterval(interval);
  }, [isLoggedIn, activeTab]);
  
  // Load messages when session is selected
  useEffect(() => {
    if (selectedSession) {
      loadMessages(selectedSession.id);
      
      // Auto-refresh messages every 3 seconds
      const interval = setInterval(() => {
        loadMessages(selectedSession.id);
      }, 3000);
      
      return () => clearInterval(interval);
    }
  }, [selectedSession]);
  
  const handleLogin = () => {
    if (agentId && agentName) {
      setIsLoggedIn(true);
      localStorage.setItem('agentId', agentId);
      localStorage.setItem('agentName', agentName);
      refreshData();
    }
  };
  
  const handleLogout = () => {
    setIsLoggedIn(false);
    setAgentId('');
    setAgentName('');
    localStorage.removeItem('agentId');
    localStorage.removeItem('agentName');
  };
  
  // Load data on mount
  useEffect(() => {
    const savedAgentId = localStorage.getItem('agentId');
    const savedAgentName = localStorage.getItem('agentName');
    
    if (savedAgentId && savedAgentName) {
      setAgentId(savedAgentId);
      setAgentName(savedAgentName);
      setIsLoggedIn(true);
    }
  }, []);
  
  const refreshData = async () => {
    if (activeTab === 'active') {
      await loadWaitingSessions();
      await loadActiveSessions();
    } else if (activeTab === 'all') {
      await loadAllSessions();
    } else if (activeTab === 'history') {
      await loadHistory();
    }
  };
  
  const loadWaitingSessions = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/agent/sessions/waiting`);
      setWaitingSessions(response.data);
    } catch (error) {
      console.error('Error loading waiting sessions:', error);
    }
  };
  
  const loadActiveSessions = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/agent/sessions/my-chats/${agentId}`);
      setActiveSessions(response.data);
    } catch (error) {
      console.error('Error loading active sessions:', error);
    }
  };
  
  const loadAllSessions = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/agent/sessions/all`);
      setAllSessions(response.data);
    } catch (error) {
      console.error('Error loading all sessions:', error);
    }
  };
  
  const loadHistory = async () => {
    try {
      const params = new URLSearchParams();
      if (searchTerm) params.append('search', searchTerm);
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      
      const response = await axios.get(`${API_URL}/api/agent/sessions/history?${params.toString()}`);
      setHistorySessions(response.data);
    } catch (error) {
      console.error('Error loading history:', error);
    }
  };
  
  const loadMessages = async (sessionId) => {
    try {
      const response = await axios.get(`${API_URL}/api/agent/sessions/${sessionId}/messages`);
      setMessages(response.data);
    } catch (error) {
      console.error('Error loading messages:', error);
    }
  };
  
  const acceptChat = async (sessionId) => {
    try {
      await axios.post(`${API_URL}/api/agent/sessions/${sessionId}/assign?agent_id=${agentId}&agent_name=${agentName}`);
      await refreshData();
      
      // Switch to Active Chats tab
      setActiveTab('active');
      
      // Load my sessions again to get the updated session with agent_id
      const response = await axios.get(`${API_URL}/api/agent/sessions/my-chats/${agentId}`);
      const updatedSession = response.data.find(s => s.id === sessionId);
      
      if (updatedSession) {
        setSelectedSession(updatedSession);
        await loadMessages(sessionId);
      }
    } catch (error) {
      console.error('Error accepting chat:', error);
      alert('Failed to accept chat');
    }
  };
  
  const sendMessage = async () => {
    if (!newMessage.trim() || !selectedSession) return;
    
    try {
      await axios.post(`${API_URL}/api/agent/sessions/${selectedSession.id}/messages`, {
        sender_type: 'agent',
        sender_id: agentId,
        message_text: newMessage
      });
      
      setNewMessage('');
      await loadMessages(selectedSession.id);
    } catch (error) {
      console.error('Error sending message:', error);
      alert('Failed to send message');
    }
  };
  
  const endChat = async (sessionId) => {
    try {
      await axios.post(`${API_URL}/api/agent/sessions/${sessionId}/end`);
      setSelectedSession(null);
      setMessages([]);
      await refreshData();
    } catch (error) {
      console.error('Error ending chat:', error);
      alert('Failed to end chat');
    }
  };
  
  const selectSession = (session) => {
    setSelectedSession(session);
    loadMessages(session.id);
  };
  
  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };
  
  // Login screen
  if (!isLoggedIn) {
    return (
      <div className="login-container">
        <div className="login-box">
          <h2>🙋 Agent Login</h2>
          <input
            type="text"
            placeholder="Agent ID"
            value={agentId}
            onChange={(e) => setAgentId(e.target.value)}
          />
          <input
            type="text"
            placeholder="Agent Name"
            value={agentName}
            onChange={(e) => setAgentName(e.target.value)}
          />
          <button onClick={handleLogin}>Login</button>
        </div>
      </div>
    );
  }
  
  // Main dashboard
  return (
    <div className="agent-dashboard">
      <div className="dashboard-header">
        <h1>🙋 Agent Dashboard</h1>
        <div className="agent-info">
          <span>👤 {agentName}</span>
          <button onClick={handleLogout}>Logout</button>
        </div>
      </div>
      
      <div className="dashboard-tabs">
        <button 
          className={activeTab === 'active' ? 'active' : ''} 
          onClick={() => { setActiveTab('active'); setSelectedSession(null); }}
        >
          Active Chats
        </button>
        <button 
          className={activeTab === 'all' ? 'active' : ''} 
          onClick={() => { setActiveTab('all'); setSelectedSession(null); }}
        >
          All Chats
        </button>
        <button 
          className={activeTab === 'history' ? 'active' : ''} 
          onClick={() => { setActiveTab('history'); setSelectedSession(null); }}
        >
          History
        </button>
      </div>
      
      <div className="dashboard-content">
        {/* Left panel - Session list */}
        <div className="sessions-panel">
          {activeTab === 'active' && (
            <>
              <div className="waiting-section">
                <h3>⏳ Waiting ({waitingSessions.length})</h3>
                {waitingSessions.map(session => (
                  <div key={session.id} className="session-card waiting">
                    <div className="session-info">
                      <div className="customer-name">{session.customer_name || session.phone_number}</div>
                      <div className="session-time">{formatTime(session.started_at)}</div>
                    </div>
                    <button onClick={() => acceptChat(session.id)} className="accept-btn">
                      ✅ Accept
                    </button>
                  </div>
                ))}
              </div>
              
              <div className="active-section">
                <h3>💬 My Chats ({activeSessions.length})</h3>
                {activeSessions.map(session => (
                  <div 
                    key={session.id} 
                    className={`session-card ${selectedSession?.id === session.id ? 'selected' : ''}`}
                    onClick={() => selectSession(session)}
                  >
                    <div className="session-info">
                      <div className="customer-name">{session.customer_name || session.phone_number}</div>
                      <div className="session-time">{formatTime(session.last_message_at || session.started_at)}</div>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
          
          {activeTab === 'all' && (
            <div className="all-section">
              <h3>📊 All Active Chats ({allSessions.length})</h3>
              {allSessions.map(session => (
                <div 
                  key={session.id} 
                  className={`session-card ${selectedSession?.id === session.id ? 'selected' : ''}`}
                  onClick={() => selectSession(session)}
                >
                  <div className="session-info">
                    <div className="customer-name">{session.customer_name || session.phone_number}</div>
                    <div className="agent-assigned">Agent: {session.agent_name || 'Waiting...'}</div>
                    <div className="session-time">{formatTime(session.last_message_at || session.started_at)}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
          
          {activeTab === 'history' && (
            <div className="history-section">
              <h3>📚 Chat History</h3>
              <div className="history-filters">
                <input
                  type="text"
                  placeholder="Search phone/name..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                />
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                />
                <button onClick={loadHistory}>🔍 Search</button>
              </div>
              
              {historySessions.map(session => (
                <div 
                  key={session.id} 
                  className={`session-card history ${selectedSession?.id === session.id ? 'selected' : ''}`}
                  onClick={() => selectSession(session)}
                >
                  <div className="session-info">
                    <div className="customer-name">{session.customer_name || session.phone_number}</div>
                    <div className="agent-assigned">Agent: {session.agent_name}</div>
                    <div className="session-time">
                      {formatTime(session.started_at)} - {formatTime(session.ended_at)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        
        {/* Right panel - Chat window */}
        <div className="chat-panel">
          {selectedSession ? (
            <>
              <div className="chat-header">
                <div>
                  <h3>{selectedSession.customer_name || selectedSession.phone_number}</h3>
                  <span className="status-badge">{selectedSession.status}</span>
                </div>
                {selectedSession.status === 'active' && selectedSession.agent_id === agentId && (
                  <button onClick={() => endChat(selectedSession.id)} className="end-btn">
                    🔚 End Chat
                  </button>
                )}
              </div>
              
              <div className="messages-container">
                {messages.map((msg, idx) => (
                  <div 
                    key={idx} 
                    className={`message ${msg.sender_type === 'agent' ? 'agent-message' : msg.sender_type === 'system' ? 'system-message' : 'customer-message'}`}
                  >
                    <div className="message-header">
                      <span className="sender">
                        {msg.sender_type === 'agent' ? '👤 Agent' : msg.sender_type === 'system' ? '🤖 System' : '👥 Customer'}
                      </span>
                      <span className="timestamp">{formatTime(msg.timestamp)}</span>
                    </div>
                    <div className="message-text">{msg.message_text}</div>
                  </div>
                ))}
              </div>
              
              {/* Show input if session is active and belongs to this agent */}
              {selectedSession.status === 'active' && selectedSession.agent_id === agentId && (
                <div className="message-input">
                  <input
                    type="text"
                    placeholder="Type a message..."
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                  />
                  <button onClick={sendMessage}>Send</button>
                </div>
              )}
              
              {/* Show waiting notice if session is still waiting */}
              {selectedSession.status === 'waiting' && (
                <div className="chat-waiting-notice">
                  ⏳ Waiting for agent to accept...
                </div>
              )}
              
              {selectedSession.status === 'ended' && (
                <div className="chat-ended-notice">
                  ✅ This chat has ended
                </div>
              )}
            </>
          ) : (
            <div className="no-chat-selected">
              <p>Select a chat to view messages</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AgentDashboard;
