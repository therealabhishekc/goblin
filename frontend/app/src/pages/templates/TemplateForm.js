import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { FiX, FiPlus, FiTrash2, FiSave } from 'react-icons/fi';
import { apiService } from '../../services/api';

const TemplateForm = ({ template, onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    template_name: '',
    template_type: 'button',
    trigger_keywords: [],
    is_active: true,
    menu_structure: {
      body: '',
      footer: '',
      steps: {
        initial: {
          type: 'button',
          buttons: [],
          next_steps: {}
        }
      }
    }
  });

  const [keywordInput, setKeywordInput] = useState('');
  const [buttonInput, setButtonInput] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (template) {
      setFormData({
        template_name: template.template_name,
        template_type: template.template_type,
        trigger_keywords: template.trigger_keywords || [],
        is_active: template.is_active,
        menu_structure: template.menu_structure || {
          body: '',
          footer: '',
          steps: {
            initial: {
              type: 'button',
              buttons: [],
              next_steps: {}
            }
          }
        }
      });
    }
  }, [template]);

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleMenuStructureChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      menu_structure: {
        ...prev.menu_structure,
        [field]: value
      }
    }));
  };

  const addKeyword = () => {
    if (keywordInput.trim() && !formData.trigger_keywords.includes(keywordInput.trim().toLowerCase())) {
      setFormData(prev => ({
        ...prev,
        trigger_keywords: [...prev.trigger_keywords, keywordInput.trim().toLowerCase()]
      }));
      setKeywordInput('');
    }
  };

  const removeKeyword = (keyword) => {
    setFormData(prev => ({
      ...prev,
      trigger_keywords: prev.trigger_keywords.filter(k => k !== keyword)
    }));
  };

  const addButton = () => {
    if (buttonInput.trim()) {
      const newButton = {
        id: buttonInput.trim().toLowerCase().replace(/\s+/g, '_'),
        title: buttonInput.trim()
      };
      
      setFormData(prev => {
        const updatedSteps = { ...prev.menu_structure.steps };
        const initialStep = { ...updatedSteps.initial };
        
        // Add button if it doesn't exist
        if (!initialStep.buttons.find(b => b.id === newButton.id)) {
          initialStep.buttons = [...(initialStep.buttons || []), newButton];
          updatedSteps.initial = initialStep;
        }
        
        return {
          ...prev,
          menu_structure: {
            ...prev.menu_structure,
            steps: updatedSteps
          }
        };
      });
      
      setButtonInput('');
    }
  };

  const removeButton = (buttonId) => {
    setFormData(prev => {
      const updatedSteps = { ...prev.menu_structure.steps };
      const initialStep = { ...updatedSteps.initial };
      
      initialStep.buttons = initialStep.buttons.filter(b => b.id !== buttonId);
      
      // Remove the next_step mapping for this button
      const nextSteps = { ...initialStep.next_steps };
      delete nextSteps[buttonId];
      initialStep.next_steps = nextSteps;
      
      updatedSteps.initial = initialStep;
      
      return {
        ...prev,
        menu_structure: {
          ...prev.menu_structure,
          steps: updatedSteps
        }
      };
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSaving(true);

    try {
      if (template) {
        // Update existing template
        await apiService.updateTemplate(template.id, {
          template_type: formData.template_type,
          trigger_keywords: formData.trigger_keywords,
          menu_structure: formData.menu_structure,
          is_active: formData.is_active
        });
      } else {
        // Create new template
        await apiService.createTemplate(formData);
      }
      
      onSuccess();
    } catch (err) {
      console.error('Error saving template:', err);
      setError(err.response?.data?.detail || 'Failed to save template');
    } finally {
      setSaving(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4 overflow-y-auto"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        onClick={(e) => e.stopPropagation()}
        className="glass-card max-w-4xl w-full my-8"
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-white">
            {template ? 'Edit Template' : 'Create Template'}
          </h2>
          <button
            onClick={onClose}
            className="p-2 rounded-lg bg-gray-500/20 text-gray-300 hover:bg-gray-500/30"
          >
            <FiX size={24} />
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Template Name *
              </label>
              <input
                type="text"
                name="template_name"
                value={formData.template_name}
                onChange={handleInputChange}
                disabled={!!template}
                required
                className="input-field w-full disabled:opacity-50 disabled:cursor-not-allowed"
                placeholder="e.g., main_menu, product_inquiry"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Template Type *
              </label>
              <select
                name="template_type"
                value={formData.template_type}
                onChange={handleInputChange}
                required
                className="input-field w-full"
              >
                <option value="button">Button Menu</option>
                <option value="list">List Menu</option>
                <option value="text">Text Only</option>
              </select>
            </div>
          </div>

          {/* Active Status */}
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="is_active"
              name="is_active"
              checked={formData.is_active}
              onChange={handleInputChange}
              className="w-4 h-4 rounded bg-gray-700 border-gray-600"
            />
            <label htmlFor="is_active" className="text-sm text-gray-300">
              Template is active
            </label>
          </div>

          {/* Trigger Keywords */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Trigger Keywords
            </label>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                value={keywordInput}
                onChange={(e) => setKeywordInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addKeyword())}
                className="input-field flex-1"
                placeholder="Enter keyword and press + (e.g., hi, hello)"
              />
              <button
                type="button"
                onClick={addKeyword}
                className="btn-primary px-4"
              >
                <FiPlus />
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {formData.trigger_keywords.map((keyword, idx) => (
                <span
                  key={idx}
                  className="flex items-center gap-2 px-3 py-1 bg-blue-500/20 text-blue-300 rounded-lg text-sm"
                >
                  {keyword}
                  <button
                    type="button"
                    onClick={() => removeKeyword(keyword)}
                    className="hover:text-red-400"
                  >
                    <FiX size={14} />
                  </button>
                </span>
              ))}
            </div>
          </div>

          {/* Menu Structure */}
          <div className="space-y-4 border border-gray-700 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-white mb-4">Menu Structure</h3>

            {/* Body Text */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Body Text *
              </label>
              <textarea
                value={formData.menu_structure.body}
                onChange={(e) => handleMenuStructureChange('body', e.target.value)}
                required
                rows={4}
                className="input-field w-full resize-none"
                placeholder="Main message body that users will see..."
              />
            </div>

            {/* Footer Text */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Footer Text (Optional)
              </label>
              <input
                type="text"
                value={formData.menu_structure.footer}
                onChange={(e) => handleMenuStructureChange('footer', e.target.value)}
                className="input-field w-full"
                placeholder="Small footer text..."
              />
            </div>

            {/* Buttons */}
            {formData.template_type === 'button' && (
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Buttons (Max 3)
                </label>
                <div className="flex gap-2 mb-2">
                  <input
                    type="text"
                    value={buttonInput}
                    onChange={(e) => setButtonInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addButton())}
                    disabled={formData.menu_structure.steps?.initial?.buttons?.length >= 3}
                    className="input-field flex-1"
                    placeholder="Button text (e.g., Explore Collection)"
                  />
                  <button
                    type="button"
                    onClick={addButton}
                    disabled={formData.menu_structure.steps?.initial?.buttons?.length >= 3}
                    className="btn-primary px-4 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <FiPlus />
                  </button>
                </div>
                <div className="space-y-2">
                  {formData.menu_structure.steps?.initial?.buttons?.map((button, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg"
                    >
                      <span className="text-white">{button.title}</span>
                      <button
                        type="button"
                        onClick={() => removeButton(button.id)}
                        className="text-red-400 hover:text-red-300"
                      >
                        <FiTrash2 />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Form Actions */}
          <div className="flex gap-3 justify-end pt-4 border-t border-gray-700">
            <button
              type="button"
              onClick={onClose}
              className="px-6 py-2 rounded-lg bg-gray-500/20 text-gray-300 hover:bg-gray-500/30"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="btn-primary px-6 py-2 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {saving ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Saving...
                </>
              ) : (
                <>
                  <FiSave />
                  {template ? 'Update' : 'Create'}
                </>
              )}
            </button>
          </div>
        </form>
      </motion.div>
    </motion.div>
  );
};

export default TemplateForm;
