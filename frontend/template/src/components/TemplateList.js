import React from 'react';
import './TemplateList.css';

function TemplateList({ templates, onEdit, onDelete }) {
  if (!templates || templates.length === 0) {
    return (
      <div className="empty-state">
        <h3>📭 No templates yet</h3>
        <p>Create your first interactive menu template to get started!</p>
      </div>
    );
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="template-list">
      <h2>Templates ({templates.length})</h2>
      <div className="template-grid">
        {templates.map((template) => (
          <div key={template.id} className={`template-card ${!template.is_active ? 'inactive' : ''}`}>
            <div className="template-header">
              <div>
                <h3>{template.template_name}</h3>
                <span className={`badge badge-${template.template_type}`}>
                  {template.template_type}
                </span>
                {!template.is_active && (
                  <span className="badge badge-inactive">Inactive</span>
                )}
              </div>
              <div className="template-actions">
                <button
                  className="btn-icon btn-edit"
                  onClick={() => onEdit(template)}
                  title="Edit"
                >
                  ✏️
                </button>
                <button
                  className="btn-icon btn-delete"
                  onClick={() => onDelete(template.id)}
                  title="Delete"
                >
                  🗑️
                </button>
              </div>
            </div>

            <div className="template-body">
              {template.trigger_keywords && template.trigger_keywords.length > 0 && (
                <div className="template-section">
                  <strong>Trigger Keywords:</strong>
                  <div className="keywords">
                    {template.trigger_keywords.map((keyword, idx) => (
                      <span key={idx} className="keyword-tag">
                        {keyword}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {template.menu_structure && (
                <div className="template-section">
                  <strong>Menu Structure:</strong>
                  <div className="menu-preview">
                    {(template.menu_structure.header_text || template.menu_structure.header?.text) && (
                      <p className="menu-text">{template.menu_structure.header_text || template.menu_structure.header?.text}</p>
                    )}
                    {(template.menu_structure.body_text || template.menu_structure.body?.text) && (
                      <p className="menu-text">{template.menu_structure.body_text || template.menu_structure.body?.text}</p>
                    )}
                    {(template.menu_structure.footer_text || template.menu_structure.footer?.text) && (
                      <p className="menu-footer">{template.menu_structure.footer_text || template.menu_structure.footer?.text}</p>
                    )}
                    {template.menu_structure.buttons && (
                      <div className="menu-buttons">
                        {template.menu_structure.buttons.map((btn, idx) => (
                          <div key={idx} className="menu-button">
                            {btn.reply?.title || btn.text || btn.title}
                          </div>
                        ))}
                      </div>
                    )}
                    {template.menu_structure.action?.buttons && (
                      <div className="menu-buttons">
                        {template.menu_structure.action.buttons.map((btn, idx) => (
                          <div key={idx} className="menu-button">
                            {btn.reply?.title || btn.text || btn.title}
                          </div>
                        ))}
                      </div>
                    )}
                    {template.menu_structure.sections && (
                      <div className="menu-sections">
                        {template.menu_structure.sections.map((section, idx) => (
                          <div key={idx} className="menu-section">
                            <strong>{section.title}</strong>
                            <ul>
                              {section.rows && section.rows.map((row, ridx) => (
                                <li key={ridx}>{row.title}</li>
                              ))}
                            </ul>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            <div className="template-footer">
              <small>Created: {formatDate(template.created_at)}</small>
              {template.updated_at !== template.created_at && (
                <small>Updated: {formatDate(template.updated_at)}</small>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default TemplateList;
