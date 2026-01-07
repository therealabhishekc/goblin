import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FiPlus, FiEdit2, FiTrash2, FiToggleLeft, FiToggleRight, FiSearch, FiMessageSquare } from 'react-icons/fi';
import { apiService } from '../../services/api';
import TemplateForm from './TemplateForm';
import '../../styles/glassmorphism.css';

const TemplateManagement = () => {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [filterActive, setFilterActive] = useState('all');
  const [showForm, setShowForm] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(null);

  useEffect(() => {
    fetchTemplates();
  }, [filterType, filterActive]);

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params = {};
      if (filterType !== 'all') params.template_type = filterType;
      if (filterActive !== 'all') params.is_active = filterActive === 'active';
      
      const response = await apiService.getTemplates(params);
      setTemplates(response.data);
    } catch (err) {
      console.error('Error fetching templates:', err);
      setError('Failed to load templates. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingTemplate(null);
    setShowForm(true);
  };

  const handleEdit = (template) => {
    setEditingTemplate(template);
    setShowForm(true);
  };

  const handleFormClose = () => {
    setShowForm(false);
    setEditingTemplate(null);
  };

  const handleFormSuccess = () => {
    setShowForm(false);
    setEditingTemplate(null);
    fetchTemplates();
  };

  const handleToggle = async (templateId) => {
    try {
      await apiService.toggleTemplateStatus(templateId);
      fetchTemplates();
    } catch (err) {
      console.error('Error toggling template:', err);
      alert('Failed to toggle template status');
    }
  };

  const handleDelete = async (templateId) => {
    try {
      await apiService.deleteTemplate(templateId);
      setDeleteConfirm(null);
      fetchTemplates();
    } catch (err) {
      console.error('Error deleting template:', err);
      alert('Failed to delete template');
    }
  };

  const filteredTemplates = templates.filter(template => 
    template.template_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    template.trigger_keywords.some(keyword => 
      keyword.toLowerCase().includes(searchTerm.toLowerCase())
    )
  );

  const getTypeIcon = (type) => {
    switch(type) {
      case 'button': return '🔘';
      case 'list': return '📋';
      case 'text': return '💬';
      default: return '📝';
    }
  };

  const getTypeBadgeClass = (type) => {
    switch(type) {
      case 'button': return 'bg-blue-500/20 text-blue-300';
      case 'list': return 'bg-purple-500/20 text-purple-300';
      case 'text': return 'bg-green-500/20 text-green-300';
      default: return 'bg-gray-500/20 text-gray-300';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="glass-card">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-gradient text-3xl font-bold mb-2">
              <FiMessageSquare className="inline mr-3" />
              Template Management
            </h1>
            <p className="text-gray-400">Create and manage interactive menu templates</p>
          </div>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleCreate}
            className="btn-primary flex items-center gap-2"
          >
            <FiPlus /> Create Template
          </motion.button>
        </div>

        {/* Filters */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Search */}
          <div className="relative">
            <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search templates..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input-field pl-10 w-full"
            />
          </div>

          {/* Type Filter */}
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="input-field"
          >
            <option value="all">All Types</option>
            <option value="button">Button Templates</option>
            <option value="list">List Templates</option>
            <option value="text">Text Templates</option>
          </select>

          {/* Active Filter */}
          <select
            value={filterActive}
            onChange={(e) => setFilterActive(e.target.value)}
            className="input-field"
          >
            <option value="all">All Status</option>
            <option value="active">Active Only</option>
            <option value="inactive">Inactive Only</option>
          </select>
        </div>
      </div>

      {/* Templates List */}
      {loading ? (
        <div className="glass-card text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="text-gray-400 mt-4">Loading templates...</p>
        </div>
      ) : error ? (
        <div className="glass-card bg-red-500/10 border border-red-500/20">
          <p className="text-red-400">{error}</p>
          <button onClick={fetchTemplates} className="btn-primary mt-4">Retry</button>
        </div>
      ) : filteredTemplates.length === 0 ? (
        <div className="glass-card text-center py-12">
          <FiMessageSquare className="text-6xl text-gray-600 mx-auto mb-4" />
          <p className="text-gray-400">No templates found</p>
          <button onClick={handleCreate} className="btn-primary mt-4">
            Create Your First Template
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {filteredTemplates.map((template) => (
            <motion.div
              key={template.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="glass-card hover:shadow-xl transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-3xl">{getTypeIcon(template.template_type)}</span>
                    <div>
                      <h3 className="text-xl font-semibold text-white">
                        {template.template_name}
                      </h3>
                      <div className="flex items-center gap-2 mt-1">
                        <span className={`text-xs px-2 py-1 rounded ${getTypeBadgeClass(template.template_type)}`}>
                          {template.template_type}
                        </span>
                        <span className={`text-xs px-2 py-1 rounded ${
                          template.is_active 
                            ? 'bg-green-500/20 text-green-300' 
                            : 'bg-gray-500/20 text-gray-400'
                        }`}>
                          {template.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Trigger Keywords */}
                  {template.trigger_keywords && template.trigger_keywords.length > 0 && (
                    <div className="mt-3">
                      <p className="text-sm text-gray-400 mb-1">Triggers:</p>
                      <div className="flex flex-wrap gap-2">
                        {template.trigger_keywords.map((keyword, idx) => (
                          <span
                            key={idx}
                            className="text-xs px-2 py-1 bg-blue-500/10 text-blue-300 rounded"
                          >
                            {keyword}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Menu Preview */}
                  <div className="mt-3">
                    <p className="text-sm text-gray-400 mb-1">Menu Structure:</p>
                    <div className="text-sm text-gray-300 bg-black/20 p-3 rounded">
                      {template.menu_structure.body && (
                        <p className="mb-2">{template.menu_structure.body.substring(0, 100)}...</p>
                      )}
                      {template.menu_structure.steps && (
                        <p className="text-xs text-gray-500">
                          Steps: {Object.keys(template.menu_structure.steps).join(', ')}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Timestamps */}
                  <div className="mt-3 text-xs text-gray-500">
                    Created: {new Date(template.created_at).toLocaleString()} | 
                    Updated: {new Date(template.updated_at).toLocaleString()}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-2 ml-4">
                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={() => handleToggle(template.id)}
                    className={`p-2 rounded-lg ${
                      template.is_active 
                        ? 'bg-green-500/20 text-green-300 hover:bg-green-500/30' 
                        : 'bg-gray-500/20 text-gray-400 hover:bg-gray-500/30'
                    }`}
                    title={template.is_active ? 'Deactivate' : 'Activate'}
                  >
                    {template.is_active ? <FiToggleRight size={20} /> : <FiToggleLeft size={20} />}
                  </motion.button>
                  
                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={() => handleEdit(template)}
                    className="p-2 rounded-lg bg-blue-500/20 text-blue-300 hover:bg-blue-500/30"
                    title="Edit"
                  >
                    <FiEdit2 size={20} />
                  </motion.button>
                  
                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={() => setDeleteConfirm(template.id)}
                    className="p-2 rounded-lg bg-red-500/20 text-red-300 hover:bg-red-500/30"
                    title="Delete"
                  >
                    <FiTrash2 size={20} />
                  </motion.button>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* Template Form Modal */}
      <AnimatePresence>
        {showForm && (
          <TemplateForm
            template={editingTemplate}
            onClose={handleFormClose}
            onSuccess={handleFormSuccess}
          />
        )}
      </AnimatePresence>

      {/* Delete Confirmation Modal */}
      <AnimatePresence>
        {deleteConfirm && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4"
            onClick={() => setDeleteConfirm(null)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="glass-card max-w-md w-full"
            >
              <h3 className="text-xl font-bold text-white mb-4">Confirm Delete</h3>
              <p className="text-gray-300 mb-6">
                Are you sure you want to delete this template? This action cannot be undone.
              </p>
              <div className="flex gap-3 justify-end">
                <button
                  onClick={() => setDeleteConfirm(null)}
                  className="px-4 py-2 rounded-lg bg-gray-500/20 text-gray-300 hover:bg-gray-500/30"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleDelete(deleteConfirm)}
                  className="px-4 py-2 rounded-lg bg-red-500/20 text-red-300 hover:bg-red-500/30"
                >
                  Delete
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default TemplateManagement;
