import React from 'react';

function BulkImportUsersView({
  file,
  loading,
  alert,
  results,
  isDragging,
  handleFileSelect,
  handleDragOver,
  handleDragLeave,
  handleDrop,
  handleUpload,
  handleReset,
  downloadTemplate
}) {
  return (
    <div className="bulk-import-container">
      <div className="bulk-import-card">
        <div className="form-header">
          <h1>📊 Bulk Import Users</h1>
          <p className="subtitle">Import multiple users at once using a CSV file</p>
        </div>

        {alert && (
          <div className={`alert alert-${alert.type}`}>
            {alert.message}
          </div>
        )}

        {/* Instructions */}
        <div className="instructions-card">
          <h3>📋 How to Import</h3>
          <ol>
            <li>Download the CSV template below</li>
            <li>Fill in your user data (one user per row)</li>
            <li>Save the file as CSV</li>
            <li>Upload the file using the form below</li>
          </ol>
          
          <button 
            type="button" 
            className="btn btn-download"
            onClick={downloadTemplate}
          >
            📥 Download CSV Template
          </button>
        </div>

        {/* CSV Format Info */}
        <div className="format-info">
          <h4>📄 CSV Format</h4>
          <div className="format-example">
            <code>
              whatsapp_phone,display_name,business_name,email,customer_tier,tags,notes
            </code>
          </div>
          <ul className="format-details">
            <li><strong>whatsapp_phone</strong> - Required (e.g., +1234567890)</li>
            <li><strong>display_name</strong> - Optional (e.g., John Doe)</li>
            <li><strong>business_name</strong> - Optional (e.g., Doe's Store)</li>
            <li><strong>email</strong> - Optional (e.g., john@example.com)</li>
            <li><strong>customer_tier</strong> - Optional: regular, premium, or vip (default: regular)</li>
            <li><strong>tags</strong> - Optional, comma-separated in quotes (e.g., "vip,regular")</li>
            <li><strong>notes</strong> - Optional (e.g., Great customer)</li>
          </ul>
        </div>

        {/* File Upload Form */}
        <form onSubmit={handleUpload} className="upload-form">
          <div 
            className={`drop-zone ${isDragging ? 'dragging' : ''} ${file ? 'has-file' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <input
              type="file"
              id="csvFile"
              accept=".csv"
              onChange={handleFileSelect}
              disabled={loading}
              style={{ display: 'none' }}
            />
            
            {!file ? (
              <label htmlFor="csvFile" className="drop-zone-label">
                <div className="drop-icon">📁</div>
                <p className="drop-text">Drag & drop your CSV file here</p>
                <p className="drop-subtext">or click to browse</p>
              </label>
            ) : (
              <div className="file-info">
                <div className="file-icon">📄</div>
                <div className="file-details">
                  <p className="file-name">{file.name}</p>
                  <p className="file-size">{(file.size / 1024).toFixed(2)} KB</p>
                </div>
                <button
                  type="button"
                  onClick={handleReset}
                  className="btn-remove-file"
                  disabled={loading}
                >
                  ✕
                </button>
              </div>
            )}
          </div>

          <div className="button-group">
            <button
              type="submit"
              className="btn btn-primary"
              disabled={!file || loading}
            >
              {loading ? '⏳ Importing...' : '📤 Upload & Import'}
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={handleReset}
              disabled={loading}
            >
              🔄 Reset
            </button>
          </div>
        </form>

        {/* Results */}
        {results && (
          <div className="results-card">
            <h3>📊 Import Results</h3>
            
            <div className="results-summary">
              <div className="result-stat">
                <div className="stat-value">{results.total}</div>
                <div className="stat-label">Total Rows</div>
              </div>
              <div className="result-stat success">
                <div className="stat-value">{results.success}</div>
                <div className="stat-label">✅ Created</div>
              </div>
              <div className="result-stat skipped">
                <div className="stat-value">{results.skipped}</div>
                <div className="stat-label">⏭️ Skipped</div>
              </div>
              <div className="result-stat failed">
                <div className="stat-value">{results.failed}</div>
                <div className="stat-label">❌ Failed</div>
              </div>
            </div>

            {/* Successfully created users */}
            {results.created_users && results.created_users.length > 0 && (
              <div className="results-section">
                <h4>✅ Successfully Created Users</h4>
                <div className="results-list">
                  {results.created_users.map((user, index) => (
                    <div key={index} className="result-item success-item">
                      <span className="result-row">Row {user.row}</span>
                      <span className="result-phone">{user.phone}</span>
                      <span className="result-name">{user.name}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Errors */}
            {results.errors && results.errors.length > 0 && (
              <div className="results-section">
                <h4>❌ Errors & Skipped</h4>
                <div className="results-list">
                  {results.errors.map((error, index) => (
                    <div key={index} className="result-item error-item">
                      <span className="result-row">Row {error.row}</span>
                      {error.phone && <span className="result-phone">{error.phone}</span>}
                      <span className="result-error">{error.error}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Tips */}
        <div className="tips-card">
          <h4>💡 Tips</h4>
          <ul>
            <li>Phone numbers must include country code (e.g., +1 for US)</li>
            <li>Duplicate phone numbers will be skipped</li>
            <li>Invalid rows will be reported in the results</li>
            <li>Empty optional fields will be left blank</li>
            <li>Maximum recommended: 1000 users per file</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default BulkImportUsersView;
