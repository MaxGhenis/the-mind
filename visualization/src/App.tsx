import React, { useState } from 'react';
import './App.css';
import DataLoader from './components/DataLoader';
import ExperimentOverview from './components/ExperimentOverview';
import GameVisualizer from './components/GameVisualizer';
import { GameData } from './types';

function App() {
  const [data, setData] = useState<GameData[]>([]);
  const [activeTab, setActiveTab] = useState<'overview' | 'visualizer'>('overview');

  const handleDataLoaded = (loadedData: GameData[]) => {
    setData(loadedData);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🧠 The Mind: LLM Coordination Research</h1>
        <p>Exploring emergent coordination in multi-agent LLM systems</p>
      </header>

      <main className="App-main">
        {data.length === 0 ? (
          <DataLoader onDataLoaded={handleDataLoaded} />
        ) : (
          <>
            <div className="tabs">
              <button 
                className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
                onClick={() => setActiveTab('overview')}
              >
                Experiment Overview
              </button>
              <button 
                className={`tab ${activeTab === 'visualizer' ? 'active' : ''}`}
                onClick={() => setActiveTab('visualizer')}
              >
                Game Visualizer
              </button>
              <button 
                className="tab reload"
                onClick={() => setData([])}
              >
                Load New Data
              </button>
            </div>

            <div className="tab-content">
              {activeTab === 'overview' && <ExperimentOverview data={data} />}
              {activeTab === 'visualizer' && <GameVisualizer data={data} />}
            </div>
          </>
        )}
      </main>

      <footer className="App-footer">
        <p>
          Paper: "Emergent Coordination in Multi-Agent LLM Systems: A Study Using The Mind Card Game"
        </p>
        <p>
          <a href="https://github.com/yourusername/the-mind" target="_blank" rel="noopener noreferrer">
            GitHub Repository
          </a>
        </p>
      </footer>
    </div>
  );
}

export default App;
