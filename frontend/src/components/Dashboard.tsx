import React, { useEffect, useState } from 'react';
import { getRecords } from '../api';
import type { TaxRecord } from '../api';

export const Dashboard: React.FC<{ refreshTrigger: number }> = ({ refreshTrigger }) => {
    const [records, setRecords] = useState<TaxRecord[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const fetchRecords = async () => {
            setLoading(true);
            try {
                const data = await getRecords();
                setRecords(data);
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchRecords();
    }, [refreshTrigger]);

    return (
        <div style={{ marginTop: '30px' }}>
            <h3>3. Vault & Extraction Data</h3>
            {loading && <p>Loading records...</p>}
            {!loading && records.length === 0 && <p>No records found.</p>}
            
            {records.length > 0 && (
                <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '10px' }}>
                    <thead>
                        <tr style={{ background: '#eee', textAlign: 'left' }}>
                            <th style={{ padding: '8px', border: '1px solid #ddd' }}>ID</th>
                            <th style={{ padding: '8px', border: '1px solid #ddd' }}>Filing Status</th>
                            <th style={{ padding: '8px', border: '1px solid #ddd' }}>W2 Wages</th>
                            <th style={{ padding: '8px', border: '1px solid #ddd' }}>Deductions</th>
                            <th style={{ padding: '8px', border: '1px solid #ddd' }}>IRA Dist</th>
                        </tr>
                    </thead>
                    <tbody>
                        {records.map(r => (
                            <tr key={r.id}>
                                <td style={{ padding: '8px', border: '1px solid #ddd' }}>{r.id}</td>
                                <td style={{ padding: '8px', border: '1px solid #ddd' }}>{r.filing_status}</td>
                                <td style={{ padding: '8px', border: '1px solid #ddd' }}>{r.w2_wages}</td>
                                <td style={{ padding: '8px', border: '1px solid #ddd' }}>{r.total_deductions}</td>
                                <td style={{ padding: '8px', border: '1px solid #ddd' }}>{r.ira_distributions}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
        </div>
    );
};
