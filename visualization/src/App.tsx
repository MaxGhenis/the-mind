import React, { useState } from 'react';
import './App.css';
import DataLoader from './components/DataLoader';
import ExperimentOverview from './components/ExperimentOverview';
import GameVisualizer from './components/GameVisualizer';
import GameAnimator from './components/GameAnimator';
import ModelComparison from './components/ModelComparison';
import { GameData } from './types';

function App() {
  const [data, setData] = useState<GameData[]>([]);
  const [activeTab, setActiveTab] = useState<'overview' | 'models' | 'visualizer' | 'animator'>('overview');

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
                className={`tab ${activeTab === 'models' ? 'active' : ''}`}
                onClick={() => setActiveTab('models')}
              >
                Model Comparison
              </button>
              <button
                className={`tab ${activeTab === 'visualizer' ? 'active' : ''}`}
                onClick={() => setActiveTab('visualizer')}
              >
                Game Visualizer
              </button>
              <button
                className={`tab ${activeTab === 'animator' ? 'active' : ''}`}
                onClick={() => setActiveTab('animator')}
              >
                Game Animator
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
              {activeTab === 'models' && <ModelComparison data={data} />}
              {activeTab === 'visualizer' && <GameVisualizer data={data} />}
              {activeTab === 'animator' && <GameAnimator data={data} />}
            </div>
          </>
        )}
      </main>

      <footer className="App-footer">
        <p>
          <strong>Research:</strong> "Emergent Coordination in Multi-Agent LLM Systems: A Study Using The Mind Card Game"
        </p>
        <p>
          Interactive visualization dashboard for analyzing multi-agent LLM coordination experiments
        </p>
      </footer>
    </div>
  );
}

export default App;
