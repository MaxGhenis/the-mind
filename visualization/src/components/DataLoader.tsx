import React, { useState, useEffect } from 'react';
import Papa from 'papaparse';
import { GameData } from '../types';

interface DataLoaderProps {
  onDataLoaded: (data: GameData[]) => void;
}

const DataLoader: React.FC<DataLoaderProps> = ({ onDataLoaded }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadSampleData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Load sample data from public folder
      const response = await fetch('/sample_data.csv');
      const text = await response.text();
      
      Papa.parse(text, {
        header: true,
        dynamicTyping: true,
        complete: (results) => {
          const data = results.data as any[];
          const processed: GameData[] = data.map(row => ({
            ...row,
            cards_played: JSON.parse(row.cards_played || '[]'),
            model_config: JSON.parse(row.model_config || '{}')
          }));
          onDataLoaded(processed);
          setLoading(false);
        },
        error: (err: any) => {
          setError(err.message);
          setLoading(false);
        }
      });
    } catch (err: any) {
      setError('Failed to load sample data');
      setLoading(false);
    }
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setError(null);

    Papa.parse(file, {
      header: true,
      dynamicTyping: true,
      complete: (results) => {
        const data = results.data as any[];
        const processed: GameData[] = data.map(row => ({
          ...row,
          cards_played: typeof row.cards_played === 'string' 
            ? JSON.parse(row.cards_played) 
            : row.cards_played,
          model_config: typeof row.model_config === 'string'
            ? JSON.parse(row.model_config)
            : row.model_config
        }));
        onDataLoaded(processed);
        setLoading(false);
      },
      error: (err: any) => {
        setError(err.message);
        setLoading(false);
      }
    });
  };

  useEffect(() => {
    // Auto-load sample data on mount
    loadSampleData();
  }, []);

  return (
    <div className="data-loader">
      <h2>Load Experiment Data</h2>
      
      <div className="loader-options">
        <button 
          onClick={loadSampleData}
          disabled={loading}
          className="btn btn-primary"
        >
          Load Sample Data
        </button>
        
        <div className="file-upload">
          <label htmlFor="csv-upload" className="btn btn-secondary">
            Upload CSV File
          </label>
          <input
            id="csv-upload"
            type="file"
            accept=".csv"
            onChange={handleFileUpload}
            disabled={loading}
            style={{ display: 'none' }}
          />
        </div>
      </div>

      {loading && <div className="loading">Loading data...</div>}
      {error && <div className="error">Error: {error}</div>}
    </div>
  );
};

export default DataLoader;