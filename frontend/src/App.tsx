import { useState } from 'react';
import { Upload } from './components/Upload';
import { Review } from './components/Review';
import { Dashboard } from './components/Dashboard';
import { getRecord } from './api';
import type { UploadResponse, TaxRecord } from './api';
import './App.css';

function App() {
  const [currentUpload, setCurrentUpload] = useState<UploadResponse | null>(null);
  const [resultRecord, setResultRecord] = useState<TaxRecord | null>(null);

  const handleUploadSuccess = (data: UploadResponse) => {
    setCurrentUpload(data);
    setResultRecord(null);
  };

  const handleApproveSuccess = async (recordId: number) => {
    try {
      const record = await getRecord(recordId);
      setResultRecord(record);
      setCurrentUpload(null);
    } catch (e) {
      console.error("Failed to fetch result record", e);
    }
  };

  const handleCancel = () => {
    setCurrentUpload(null);
  };

  const handleStartOver = () => {
    setResultRecord(null);
    setCurrentUpload(null);
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      <h1>Google Cloud File Vault</h1>
      <p>Secure PII Redaction & Extraction Pipeline</p>
      
      {!currentUpload && !resultRecord && <Upload onUploadSuccess={handleUploadSuccess} />}
      
      {currentUpload && (
        <Review 
          uploadData={currentUpload} 
          onApproveSuccess={handleApproveSuccess} 
          onCancel={handleCancel}
        />
      )}

      {resultRecord && (
        <div>
          <Dashboard record={resultRecord} />
          <div style={{ marginTop: '20px', textAlign: 'center' }}>
            <button 
              onClick={handleStartOver}
              style={{ padding: '10px 20px', fontSize: '16px', cursor: 'pointer' }}
            >
              Start New Upload
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;