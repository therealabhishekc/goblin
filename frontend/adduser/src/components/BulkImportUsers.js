import React, { useState } from 'react';
import './BulkImportUsers.css';
import BulkImportUsersView from './BulkImportUsersView';

function BulkImportUsers() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [alert, setAlert] = useState(null);
  const [results, setResults] = useState(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      if (selectedFile.name.endsWith('.csv')) {
        setFile(selectedFile);
        setAlert({ type: 'info', message: `📄 File selected: ${selectedFile.name}` });
        setResults(null);
      } else {
        setAlert({ type: 'error', message: '❌ Please select a CSV file' });
        setFile(null);
      }
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      if (droppedFile.name.endsWith('.csv')) {
        setFile(droppedFile);
        setAlert({ type: 'info', message: `📄 File selected: ${droppedFile.name}` });
        setResults(null);
      } else {
        setAlert({ type: 'error', message: '❌ Please drop a CSV file' });
      }
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    
    if (!file) {
      setAlert({ type: 'error', message: '❌ Please select a CSV file first' });
      return;
    }

    setLoading(true);
    setAlert(null);
    setResults(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(
        'https://hwwsxxpemc.us-east-1.awsapprunner.com/api/users/bulk-import',
        {
          method: 'POST',
          body: formData
        }
      );

      const result = await response.json();

      if (response.ok) {
        setResults(result);
        
        if (result.failed === 0 && result.skipped === 0) {
          setAlert({ 
            type: 'success', 
            message: `✅ All ${result.success} users imported successfully!` 
          });
        } else if (result.success > 0) {
          setAlert({ 
            type: 'warning', 
            message: `⚠️ Partially completed: ${result.success} created, ${result.skipped} skipped, ${result.failed} failed` 
          });
        } else {
          setAlert({ 
            type: 'error', 
            message: `❌ Import failed: ${result.failed} errors, ${result.skipped} skipped` 
          });
        }
        
        // Clear file after successful upload
        if (result.success > 0) {
          setFile(null);
        }
      } else {
        setAlert({ 
          type: 'error', 
          message: `❌ Error: ${result.detail || 'Failed to import users'}` 
        });
      }
    } catch (error) {
      setAlert({ 
        type: 'error', 
        message: `❌ Network Error: ${error.message}. Make sure backend is running.` 
      });
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setAlert(null);
    setResults(null);
  };

  const downloadTemplate = () => {
    const csvContent = `whatsapp_phone,display_name,business_name,email,customer_tier,tags,notes
+1234567890,John Doe,Doe's Store,john@example.com,premium,"vip,regular",Great customer
+0987654321,Jane Smith,Smith Co,jane@example.com,regular,"new",First time buyer
+1122334455,Bob Johnson,Bob's Shop,bob@example.com,vip,"vip,loyal",Top customer`;

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'bulk_import_template.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    
    setAlert({ type: 'info', message: '📥 Template downloaded successfully!' });
  };

  return (
    <BulkImportUsersView
      file={file}
      loading={loading}
      alert={alert}
      results={results}
      isDragging={isDragging}
      handleFileSelect={handleFileSelect}
      handleDragOver={handleDragOver}
      handleDragLeave={handleDragLeave}
      handleDrop={handleDrop}
      handleUpload={handleUpload}
      handleReset={handleReset}
      downloadTemplate={downloadTemplate}
    />
  );
}

export default BulkImportUsers;
