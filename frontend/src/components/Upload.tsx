import React, { useState } from 'react';
import { uploadFile } from '../api';
import type { UploadResponse } from '../api';

interface UploadProps {
    onUploadSuccess: (data: UploadResponse) => void;
}

export const Upload: React.FC<UploadProps> = ({ onUploadSuccess }) => {
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
        if (event.target.files && event.target.files.length > 0) {
            const file = event.target.files[0];
            setUploading(true);
            setError(null);
            
            try {
                const response = await uploadFile(file);
                onUploadSuccess(response);
            } catch (err: any) {
                console.error(err);
                setError("Upload failed. Please try again.");
            } finally {
                setUploading(false);
            }
        }
    };

    return (
        <div style={{ border: '1px dashed #ccc', padding: '20px', marginBottom: '20px' }}>
            <h3>1. Secure Upload</h3>
            <p>Select a PDF to upload to the Secure Quarantine Zone.</p>
            <input 
                type="file" 
                accept="application/pdf" 
                onChange={handleFileChange} 
                disabled={uploading}
            />
            {uploading && <p>Uploading and Sanitizing...</p>}
            {error && <p style={{ color: 'red' }}>{error}</p>}
        </div>
    );
};
