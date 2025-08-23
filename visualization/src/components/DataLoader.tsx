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
      // Load sample data from public folder (use relative path for dev)
      const url = process.env.PUBLIC_URL + '/sample_data.csv';
      console.log('Fetching from:', url);
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const text = await response.text();
      console.log('Fetched text length:', text.length);
      
      Papa.parse(text, {
        header: true,
        dynamicTyping: true,
        complete: (results) => {
          const data = results.data as any[];
          console.log('Parsed rows:', data.length);
          console.log('First row sample:', data[0]);
          
          const processed: GameData[] = data
            .filter(row => row && row.game_id) // Filter out empty rows
            .map(row => {
              try {
                return {
                  ...row,
                  // Parse boolean fields properly
                  success: row.success === true || row.success === 'true' || row.success === 'True',
                  use_memory: row.use_memory === true || row.use_memory === 'true' || row.use_memory === 'True',
                  final_success: row.final_success === true || row.final_success === 'true' || row.final_success === 'True',
                  // Parse JSON fields
                  cards_played: typeof row.cards_played === 'string' 
                    ? JSON.parse(row.cards_played || '[]')
                    : row.cards_played || [],
                  model_config: typeof row.model_config === 'string'
                    ? JSON.parse(row.model_config || '{}')
                    : row.model_config || {},
                  // Parse action_data if present
                  action_data: row.action_data && typeof row.action_data === 'string'
                    ? JSON.parse(row.action_data)
                    : row.action_data
                };
              } catch (e) {
                console.error('Error processing row:', row, e);
                return null;
              }
            })
            .filter(row => row !== null) as GameData[];
          
          console.log('Processed data:', processed.length, 'rows');
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
        const processed: GameData[] = data
          .filter(row => row && row.game_id)
          .map(row => ({
            ...row,
            // Parse boolean fields properly
            success: row.success === true || row.success === 'true' || row.success === 'True',
            use_memory: row.use_memory === true || row.use_memory === 'true' || row.use_memory === 'True',
            final_success: row.final_success === true || row.final_success === 'true' || row.final_success === 'True',
            // Parse JSON fields
            cards_played: typeof row.cards_played === 'string' 
              ? JSON.parse(row.cards_played) 
              : row.cards_played,
            model_config: typeof row.model_config === 'string'
              ? JSON.parse(row.model_config)
              : row.model_config,
            // Parse action_data if present
            action_data: row.action_data && typeof row.action_data === 'string'
              ? JSON.parse(row.action_data)
              : row.action_data
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
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