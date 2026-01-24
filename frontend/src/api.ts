import axios from 'axios';

// In a real app, use import.meta.env.VITE_API_URL
const API_URL = import.meta.env.VITE_API_URL || '';

export interface TaxRecord {
    id: number;
    user_id: string;
    filing_status: string | null;
    w2_wages: number | null;
    total_deductions: number | null;
    ira_distributions: number | null;
    capital_gain_loss: number | null;
}

export interface UploadResponse {
    status: string;
    correlation_id: string;
    preview_url: string;
}

// Simple user ID simulation
const USER_ID = 'test-user-123';

const apiClient = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
        'X-User-ID': USER_ID
    }
});

export const uploadFile = async (file: File): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await apiClient.post('/upload', formData, {
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    });
    return response.data;
};

export const approveDocument = async (correlationId: string) => {
    const response = await apiClient.post(`/approve/${correlationId}`);
    return response.data;
};

export const getRecords = async (): Promise<TaxRecord[]> => {
    const response = await apiClient.get('/records');
    return response.data;
};
