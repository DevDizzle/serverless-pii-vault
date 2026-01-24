import React, { useState } from 'react';
import { approveDocument } from '../api';
import type { UploadResponse } from '../api';

interface ReviewProps {
    uploadData: UploadResponse;
    onApproveSuccess: () => void;
    onCancel: () => void;
}

export const Review: React.FC<ReviewProps> = ({ uploadData, onApproveSuccess, onCancel }) => {
    const [approving, setApproving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleApprove = async () => {
        setApproving(true);
        setError(null);
        try {
            await approveDocument(uploadData.correlation_id);
            onApproveSuccess();
        } catch (err: any) {
            console.error(err);
            setError("Approval failed.");
        } finally {
            setApproving(false);
        }
    };

    return (
        <div style={{ border: '1px solid #ccc', padding: '20px', marginBottom: '20px' }}>
            <h3>2. Review Redaction</h3>
            <p>Please review the sanitized document below. PII should be blacked out.</p>
            
            <div style={{ background: '#f0f0f0', padding: '10px', marginBottom: '10px' }}>
                <strong>Preview URL:</strong> <a href={uploadData.preview_url} target="_blank" rel="noreferrer">{uploadData.preview_url}</a>
                <p><em>(In a real deployment, this would be an embedded PDF viewer)</em></p>
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
                <button onClick={handleApprove} disabled={approving} style={{ background: 'green', color: 'white', padding: '10px' }}>
                    {approving ? "Processing..." : "Approve & Extract Data"}
                </button>
                <button onClick={onCancel} disabled={approving} style={{ background: 'red', color: 'white', padding: '10px' }}>
                    Reject
                </button>
            </div>
            {error && <p style={{ color: 'red' }}>{error}</p>}
        </div>
    );
};
