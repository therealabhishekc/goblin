import React, { useState, useEffect } from 'react';
import './TemplateForm.css';

function TemplateForm({ template, onSubmit, onCancel }) {
  const [formData, setFormData] = useState({
    template_name: '',
    template_type: 'button',
    trigger_keywords: '',
    is_active: true,
    menu_structure: {
      header_text: '',
      body_text: '',
      footer_text: '',
      buttons: []
    }
  });
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (template) {
      // Parse the actual menu_structure from database
      const menuStruct = template.menu_structure || {};
      
      // Extract values from the database structure
      const headerText = menuStruct.header?.text || '';
      const bodyText = menuStruct.body?.text || '';
      const footerText = menuStruct.footer?.text || '';
      const buttons = menuStruct.action?.buttons || [];
      
      setFormData({
        template_name: template.template_name || '',
        template_type: template.template_type || 'button',
        trigger_keywords: template.trigger_keywords ? template.trigger_keywords.join(', ') : '',
        is_active: template.is_active !== undefined ? template.is_active : true,
        menu_structure: {
          header_text: headerText,
          body_text: bodyText,
          footer_text: footerText,
          buttons: buttons
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

  const handleButtonChange = (index, field, value) => {
    const newButtons = [...formData.menu_structure.buttons];
    newButtons[index] = {
      ...newButtons[index],
      [field]: value
    };
    handleMenuStructureChange('buttons', newButtons);
  };

  const addButton = () => {
    const newButtons = [...(formData.menu_structure.buttons || [])];
    newButtons.push({ type: 'reply', reply: { id: '', title: '' } });
    handleMenuStructureChange('buttons', newButtons);
  };

  const removeButton = (index) => {
    const newButtons = formData.menu_structure.buttons.filter((_, i) => i !== index);
    handleMenuStructureChange('buttons', newButtons);
  };

  const validate = () => {
    const newErrors = {};

    if (!formData.template_name.trim()) {
      newErrors.template_name = 'Template name is required';
    }

    if (!formData.template_type) {
      newErrors.template_type = 'Template type is required';
    }

    if (!formData.menu_structure.body_text.trim()) {
      newErrors.body_text = 'Body text is required';
    }

    if (formData.template_type === 'button' && (!formData.menu_structure.buttons || formData.menu_structure.buttons.length === 0)) {
      newErrors.buttons = 'At least one button is required for button templates';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validate()) {
      return;
    }

    setSubmitting(true);
    setErrors({});

    try {
      // Process trigger keywords
      const keywords = formData.trigger_keywords
        .split(',')
        .map(k => k.trim().toLowerCase())
        .filter(k => k);

      // Prepare buttons for submission
      const buttons = formData.menu_structure.buttons.map(btn => ({
        type: 'reply',
        reply: {
          id: btn.reply?.id || btn.reply?.title?.toLowerCase().replace(/\s+/g, '_') || '',
          title: btn.reply?.title || ''
        }
      }));

      // Format menu_structure to match backend expectations
      const menuStructure = {
        type: formData.template_type,
      };

      // Add body text if present
      if (formData.menu_structure.body_text) {
        menuStructure.body = {
          text: formData.menu_structure.body_text
        };
      }

      // Add header text if present
      if (formData.menu_structure.header_text) {
        menuStructure.header = {
          text: formData.menu_structure.header_text
        };
      }

      // Add footer text if present
      if (formData.menu_structure.footer_text) {
        menuStructure.footer = {
          text: formData.menu_structure.footer_text
        };
      }

      // Add buttons/action if button type
      if (formData.template_type === 'button' && buttons.length > 0) {
        menuStructure.action = {
          buttons: buttons
        };
      }

      // Add initial step configuration
      menuStructure.steps = {
        initial: {
          prompt: formData.menu_structure.body_text
        }
      };

      const submitData = {
        template_name: formData.template_name,
        template_type: formData.template_type,
        trigger_keywords: keywords,
        is_active: formData.is_active,
        menu_structure: menuStructure
      };

      await onSubmit(submitData);
    } catch (err) {
      setErrors({ submit: err.message || 'Failed to save template' });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="template-form-container">
      <div className="template-form-card">
        <h2>{template ? '✏️ Edit Template' : '➕ Create New Template'}</h2>
        
        <form onSubmit={handleSubmit} className="template-form">
          {errors.submit && (
            <div className="form-error">{errors.submit}</div>
          )}

          <div className="form-group">
            <label htmlFor="template_name">
              Template Name <span className="required">*</span>
            </label>
            <input
              type="text"
              id="template_name"
              name="template_name"
              value={formData.template_name}
              onChange={handleInputChange}
              placeholder="e.g., main_menu, product_catalog"
              disabled={!!template}
            />
            {errors.template_name && <span className="error">{errors.template_name}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="template_type">
              Template Type <span className="required">*</span>
            </label>
            <select
              id="template_type"
              name="template_type"
              value={formData.template_type}
              onChange={handleInputChange}
            >
              <option value="button">Button</option>
              <option value="list">List</option>
              <option value="text">Text</option>
            </select>
            {errors.template_type && <span className="error">{errors.template_type}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="trigger_keywords">
              Trigger Keywords (comma-separated)
            </label>
            <input
              type="text"
              id="trigger_keywords"
              name="trigger_keywords"
              value={formData.trigger_keywords}
              onChange={handleInputChange}
              placeholder="e.g., hi, hello, start, menu"
            />
            <small>Keywords that will trigger this template (case-insensitive)</small>
          </div>

          <div className="form-group checkbox-group">
            <label>
              <input
                type="checkbox"
                name="is_active"
                checked={formData.is_active}
                onChange={handleInputChange}
              />
              <span>Active Template</span>
            </label>
          </div>

          <div className="form-section">
            <h3>Menu Structure</h3>

            <div className="form-group">
              <label htmlFor="header_text">Header Text</label>
              <input
                type="text"
                id="header_text"
                value={formData.menu_structure.header_text || ''}
                onChange={(e) => handleMenuStructureChange('header_text', e.target.value)}
                placeholder="Optional header text"
              />
            </div>

            <div className="form-group">
              <label htmlFor="body_text">
                Body Text <span className="required">*</span>
              </label>
              <textarea
                id="body_text"
                value={formData.menu_structure.body_text || ''}
                onChange={(e) => handleMenuStructureChange('body_text', e.target.value)}
                placeholder="Main message text"
                rows="4"
              />
              {errors.body_text && <span className="error">{errors.body_text}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="footer_text">Footer Text</label>
              <input
                type="text"
                id="footer_text"
                value={formData.menu_structure.footer_text || ''}
                onChange={(e) => handleMenuStructureChange('footer_text', e.target.value)}
                placeholder="Optional footer text"
              />
            </div>

            {formData.template_type === 'button' && (
              <div className="form-group">
                <label>
                  Buttons <span className="required">*</span>
                </label>
                {errors.buttons && <span className="error">{errors.buttons}</span>}
                
                <div className="buttons-list">
                  {formData.menu_structure.buttons && formData.menu_structure.buttons.map((button, index) => (
                    <div key={index} className="button-item">
                      <input
                        type="text"
                        value={button.reply?.title || ''}
                        onChange={(e) => handleButtonChange(index, 'reply', { 
                          ...button.reply, 
                          title: e.target.value,
                          id: e.target.value.toLowerCase().replace(/\s+/g, '_')
                        })}
                        placeholder={`Button ${index + 1} text`}
                      />
                      <button
                        type="button"
                        className="btn-remove"
                        onClick={() => removeButton(index)}
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                </div>
                
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={addButton}
                >
                  ➕ Add Button
                </button>
                <small>Maximum 3 buttons allowed by WhatsApp</small>
              </div>
            )}
          </div>

          <div className="form-actions">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onCancel}
              disabled={submitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={submitting}
            >
              {submitting ? 'Saving...' : (template ? 'Update Template' : 'Create Template')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default TemplateForm;
