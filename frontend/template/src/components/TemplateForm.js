import React, { useState, useEffect } from 'react';
import './TemplateForm.css';

function TemplateForm({ template, onSubmit, onCancel }) {
  const [formData, setFormData] = useState({
    template_name: '',
    template_type: 'button',
    trigger_keywords: '',
    is_active: true,
    menu_structure: {
      header_type: 'text',
      header_text: '',
      header_media_id: '',
      header_media_link: '',
      header_filename: '',
      body_text: '',
      footer_text: '',
      buttons: []
    },
    steps: {
      initial: {
        prompt: '',
        next_steps: {}
      }
    },
    currentStepName: 'initial'
  });
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (template) {
      // Parse the actual menu_structure from database
      const menuStruct = template.menu_structure || {};
      
      // Extract values from the database structure
      const header = menuStruct.header || {};
      const headerType = header.type || 'text';
      const headerText = header.text || '';
      
      // Handle media - check both nested structure and direct link/id
      let headerMediaId = '';
      let headerMediaLink = '';
      let headerFilename = '';
      
      if (headerType === 'image') {
        headerMediaId = header.image?.id || header.id || '';
        headerMediaLink = header.image?.link || header.link || '';
      } else if (headerType === 'video') {
        headerMediaId = header.video?.id || header.id || '';
        headerMediaLink = header.video?.link || header.link || '';
      } else if (headerType === 'document') {
        headerMediaId = header.document?.id || header.id || '';
        headerMediaLink = header.document?.link || header.link || '';
        headerFilename = header.document?.filename || header.filename || '';
      }
      
      const bodyText = menuStruct.body?.text || '';
      const footerText = menuStruct.footer?.text || '';
      const buttons = menuStruct.action?.buttons || [];
      const steps = menuStruct.steps || { initial: { prompt: bodyText, next_steps: {} } };
      // Get the first step name as current (usually 'initial')
      const currentStepName = Object.keys(steps)[0] || 'initial';
      
      setFormData({
        template_name: template.template_name || '',
        template_type: template.template_type || 'button',
        trigger_keywords: template.trigger_keywords ? template.trigger_keywords.join(', ') : '',
        is_active: template.is_active !== undefined ? template.is_active : true,
        menu_structure: {
          header_type: headerType,
          header_text: headerText,
          header_media_id: headerMediaId,
          header_media_link: headerMediaLink,
          header_filename: headerFilename,
          body_text: bodyText,
          footer_text: footerText,
          buttons: buttons
        },
        steps: steps,
        currentStepName: currentStepName
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
    
    // If changing the reply ID, update the next_steps mapping
    if (field === 'reply.id') {
      const oldId = newButtons[index]?.reply?.id;
      const newId = value;
      
      // Update button
      newButtons[index] = {
        ...newButtons[index],
        reply: {
          ...newButtons[index].reply,
          id: newId
        }
      };
      
      // Update next_steps mapping if old ID existed
      const currentStep = formData.currentStepName;
      if (oldId && formData.steps?.[currentStep]?.next_steps?.[oldId]) {
        const nextSteps = { ...formData.steps[currentStep].next_steps };
        const targetStep = nextSteps[oldId];
        delete nextSteps[oldId];
        if (newId) {
          nextSteps[newId] = targetStep;
        }
        setFormData(prev => ({
          ...prev,
          steps: {
            ...prev.steps,
            [currentStep]: {
              ...prev.steps[currentStep],
              next_steps: nextSteps
            }
          }
        }));
      }
    } else if (field === 'reply.title') {
      newButtons[index] = {
        ...newButtons[index],
        reply: {
          ...newButtons[index].reply,
          title: value
        }
      };
    } else {
      newButtons[index] = {
        ...newButtons[index],
        [field]: value
      };
    }
    
    handleMenuStructureChange('buttons', newButtons);
  };

  const addButton = () => {
    const newButtons = [...(formData.menu_structure.buttons || [])];
    newButtons.push({ type: 'reply', reply: { id: '', title: '' } });
    handleMenuStructureChange('buttons', newButtons);
  };

  const removeButton = (index) => {
    const buttonToRemove = formData.menu_structure.buttons[index];
    const buttonId = buttonToRemove?.reply?.id;
    
    // Remove button
    const newButtons = formData.menu_structure.buttons.filter((_, i) => i !== index);
    handleMenuStructureChange('buttons', newButtons);
    
    // Remove from next_steps if exists
    const currentStep = formData.currentStepName;
    if (buttonId && formData.steps?.[currentStep]?.next_steps?.[buttonId]) {
      const nextSteps = { ...formData.steps[currentStep].next_steps };
      delete nextSteps[buttonId];
      setFormData(prev => ({
        ...prev,
        steps: {
          ...prev.steps,
          [currentStep]: {
            ...prev.steps[currentStep],
            next_steps: nextSteps
          }
        }
      }));
    }
  };

  const handleNextStepChange = (buttonId, targetStep) => {
    setFormData(prev => ({
      ...prev,
      steps: {
        ...prev.steps,
        [prev.currentStepName]: {
          ...prev.steps[prev.currentStepName],
          next_steps: {
            ...prev.steps[prev.currentStepName].next_steps,
            [buttonId]: targetStep
          }
        }
      }
    }));
  };

  const handleInitialPromptChange = (value) => {
    setFormData(prev => ({
      ...prev,
      steps: {
        ...prev.steps,
        [prev.currentStepName]: {
          ...prev.steps[prev.currentStepName],
          prompt: value
        }
      }
    }));
  };

  const handleStepNameChange = (newStepName) => {
    const oldStepName = formData.currentStepName;
    
    if (newStepName === oldStepName) return;
    if (!newStepName.trim()) return;
    
    // Rename the step
    const newSteps = { ...formData.steps };
    newSteps[newStepName] = { ...newSteps[oldStepName] };
    delete newSteps[oldStepName];
    
    setFormData(prev => ({
      ...prev,
      steps: newSteps,
      currentStepName: newStepName
    }));
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

    // Validate button titles if buttons exist
    if (formData.template_type === 'button' && formData.menu_structure.buttons && formData.menu_structure.buttons.length > 0) {
      const invalidButtons = formData.menu_structure.buttons.filter(btn => !btn.reply?.title?.trim());
      if (invalidButtons.length > 0) {
        newErrors.buttons = 'All buttons must have a title';
      }
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
      const buttons = formData.menu_structure.buttons.map(btn => {
        const title = btn.reply?.title || '';
        const id = btn.reply?.id || title.toLowerCase().replace(/\s+/g, '_');
        
        if (!title.trim()) {
          throw new Error('All buttons must have a title');
        }
        
        return {
          type: 'reply',
          reply: {
            id: id || `button_${Date.now()}`, // Fallback to timestamp if still empty
            title: title
          }
        };
      });

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

      // Add header based on type
      const headerType = formData.menu_structure.header_type;
      if (headerType === 'text' && formData.menu_structure.header_text) {
        menuStructure.header = {
          type: 'text',
          text: formData.menu_structure.header_text
        };
      } else if (headerType === 'image') {
        if (formData.menu_structure.header_media_id) {
          menuStructure.header = {
            type: 'image',
            id: formData.menu_structure.header_media_id
          };
        } else if (formData.menu_structure.header_media_link) {
          menuStructure.header = {
            type: 'image',
            link: formData.menu_structure.header_media_link
          };
        }
      } else if (headerType === 'video') {
        if (formData.menu_structure.header_media_id) {
          menuStructure.header = {
            type: 'video',
            id: formData.menu_structure.header_media_id
          };
        } else if (formData.menu_structure.header_media_link) {
          menuStructure.header = {
            type: 'video',
            link: formData.menu_structure.header_media_link
          };
        }
      } else if (headerType === 'document') {
        if (formData.menu_structure.header_media_id) {
          menuStructure.header = {
            type: 'document',
            id: formData.menu_structure.header_media_id
          };
          if (formData.menu_structure.header_filename) {
            menuStructure.header.filename = formData.menu_structure.header_filename;
          }
        } else if (formData.menu_structure.header_media_link) {
          menuStructure.header = {
            type: 'document',
            link: formData.menu_structure.header_media_link
          };
          if (formData.menu_structure.header_filename) {
            menuStructure.header.filename = formData.menu_structure.header_filename;
          }
        }
      } else if (headerType === 'none') {
        // No header
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

      // Add steps configuration
      if (formData.steps && Object.keys(formData.steps).length > 0) {
        menuStructure.steps = formData.steps;
      } else {
        // Default steps if not configured
        const stepName = formData.currentStepName || 'initial';
        menuStructure.steps = {
          [stepName]: {
            prompt: formData.menu_structure.body_text,
            next_steps: {}
          }
        };
      }

      const submitData = {
        template_name: formData.template_name,
        template_type: formData.template_type,
        trigger_keywords: keywords,
        is_active: formData.is_active,
        menu_structure: menuStructure
      };

      console.log('📤 Submitting template data:', JSON.stringify(submitData, null, 2));
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
              <label htmlFor="header_type">Header Type</label>
              <select
                id="header_type"
                value={formData.menu_structure.header_type || 'text'}
                onChange={(e) => handleMenuStructureChange('header_type', e.target.value)}
              >
                <option value="none">No Header</option>
                <option value="text">Text</option>
                <option value="image">Image</option>
                <option value="video">Video</option>
                <option value="document">Document</option>
              </select>
            </div>

            {formData.menu_structure.header_type === 'text' && (
              <div className="form-group">
                <label htmlFor="header_text">Header Text</label>
                <input
                  type="text"
                  id="header_text"
                  value={formData.menu_structure.header_text || ''}
                  onChange={(e) => handleMenuStructureChange('header_text', e.target.value)}
                  placeholder="Enter header text"
                />
              </div>
            )}

            {['image', 'video', 'document'].includes(formData.menu_structure.header_type) && (
              <>
                <div className="form-group">
                  <label htmlFor="header_media_id">Media ID</label>
                  <input
                    type="text"
                    id="header_media_id"
                    value={formData.menu_structure.header_media_id || ''}
                    onChange={(e) => handleMenuStructureChange('header_media_id', e.target.value)}
                    placeholder="WhatsApp Media ID"
                  />
                  <small>Use Media ID (uploaded to WhatsApp) OR Link below</small>
                </div>

                <div className="form-group">
                  <label htmlFor="header_media_link">Media Link (URL)</label>
                  <input
                    type="text"
                    id="header_media_link"
                    value={formData.menu_structure.header_media_link || ''}
                    onChange={(e) => handleMenuStructureChange('header_media_link', e.target.value)}
                    placeholder="https://example.com/media.jpg"
                  />
                  <small>Public URL to the media file</small>
                </div>

                {formData.menu_structure.header_type === 'document' && (
                  <div className="form-group">
                    <label htmlFor="header_filename">Filename</label>
                    <input
                      type="text"
                      id="header_filename"
                      value={formData.menu_structure.header_filename || ''}
                      onChange={(e) => handleMenuStructureChange('header_filename', e.target.value)}
                      placeholder="document.pdf"
                    />
                    <small>Filename for the document (optional)</small>
                  </div>
                )}
              </>
            )}

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
                    <div key={index} className="button-item-enhanced">
                      <div className="button-header">
                        <strong>Button {index + 1}</strong>
                        <button
                          type="button"
                          className="btn-remove"
                          onClick={() => removeButton(index)}
                        >
                          ✕
                        </button>
                      </div>
                      
                      <div className="button-fields">
                        <div className="form-group-inline">
                          <label>Button ID *</label>
                          <input
                            type="text"
                            value={button.reply?.id || ''}
                            onChange={(e) => handleButtonChange(index, 'reply.id', e.target.value)}
                            placeholder="unique_button_id"
                          />
                          <small>Unique identifier for this button</small>
                        </div>
                        
                        <div className="form-group-inline">
                          <label>Button Title *</label>
                          <input
                            type="text"
                            value={button.reply?.title || ''}
                            onChange={(e) => handleButtonChange(index, 'reply.title', e.target.value)}
                            placeholder="Button text (max 20 chars)"
                            maxLength="20"
                          />
                          <small>Text shown on button (max 20 characters)</small>
                        </div>
                        
                        <div className="form-group-inline">
                          <label>Next Step →</label>
                          <input
                            type="text"
                            value={formData.steps?.[formData.currentStepName]?.next_steps?.[button.reply?.id] || ''}
                            onChange={(e) => handleNextStepChange(button.reply?.id, e.target.value)}
                            placeholder="template_name or step_name"
                            disabled={!button.reply?.id}
                          />
                          <small>Template name or step name to navigate to when clicked</small>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={addButton}
                  disabled={formData.menu_structure.buttons.length >= 3}
                >
                  ➕ Add Button
                </button>
                <small>Maximum 3 buttons allowed by WhatsApp</small>
              </div>
            )}

            {formData.template_type === 'button' && formData.menu_structure.buttons.length > 0 && (
              <div className="steps-preview">
                <h4>📍 Flow Configuration</h4>
                
                <div className="form-group">
                  <label htmlFor="step_name">Step Name</label>
                  <input
                    type="text"
                    id="step_name"
                    value={formData.currentStepName}
                    onChange={(e) => handleStepNameChange(e.target.value)}
                    placeholder="initial"
                  />
                  <small>Unique identifier for this step (e.g., 'initial', 'collect_info', 'confirm')</small>
                </div>
                
                <div className="flow-summary">
                  <p><strong>Current Step:</strong> <code>{formData.currentStepName}</code></p>
                  <p><strong>Step Prompt:</strong> {formData.steps?.[formData.currentStepName]?.prompt || formData.menu_structure.body_text || '(using body text)'}</p>
                  <p><strong>Button Mappings:</strong></p>
                  <ul>
                    {formData.menu_structure.buttons.map((button, index) => {
                      const buttonId = button.reply?.id;
                      const buttonTitle = button.reply?.title;
                      const nextStep = formData.steps?.[formData.currentStepName]?.next_steps?.[buttonId];
                      return (
                        <li key={index}>
                          <code>{buttonId || '(no id)'}</code> - "{buttonTitle || '(no title)'}" → {nextStep || <em>(end conversation)</em>}
                        </li>
                      );
                    })}
                  </ul>
                </div>
                
                <div className="form-group">
                  <label htmlFor="step_prompt">Step Prompt (optional)</label>
                  <textarea
                    id="step_prompt"
                    value={formData.steps?.[formData.currentStepName]?.prompt || ''}
                    onChange={(e) => handleInitialPromptChange(e.target.value)}
                    placeholder="Leave empty to use body text as prompt"
                    rows="2"
                  />
                  <small>Custom message for this step (defaults to body text)</small>
                </div>
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
