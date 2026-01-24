import { useState } from 'react';
import { Upload } from './components/Upload';
import { Review } from './components/Review';
import { Dashboard } from './components/Dashboard';
import type { UploadResponse } from './api';
import './App.css';

function App() {
  const [currentUpload, setCurrentUpload] = useState<UploadResponse | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleUploadSuccess = (data: UploadResponse) => {
    setCurrentUpload(data);
  };

  const handleApproveSuccess = () => {
    setCurrentUpload(null);
    setRefreshTrigger(prev => prev + 1); // Refresh dashboard
  };

  const handleCancel = () => {
    setCurrentUpload(null);
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      <h1>Google Cloud File Vault</h1>
      <p>Secure PII Redaction & Extraction Pipeline</p>
      
      {!currentUpload && <Upload onUploadSuccess={handleUploadSuccess} />}
      
      {currentUpload && (
        <Review 
          uploadData={currentUpload} 
          onApproveSuccess={handleApproveSuccess} 
          onCancel={handleCancel}
        />
      )}

      <Dashboard refreshTrigger={refreshTrigger} />
    </div>
  );
}

export default App;