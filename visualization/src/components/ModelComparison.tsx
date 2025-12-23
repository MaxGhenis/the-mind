import React from 'react';
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, Tooltip, ScatterChart, Scatter,
  XAxis, YAxis, CartesianGrid, Cell
} from 'recharts';
import { GameData } from '../types';

interface ModelComparisonProps {
  data: GameData[];
}

const ModelComparison: React.FC<ModelComparisonProps> = ({ data }) => {
  // Extract unique models from the data
  const getModelStats = () => {
    const modelMap = new Map<string, {
      totalGames: number;
      successfulGames: number;
      totalRounds: number;
      totalTime: number;
      avgDecisionTime: number;
      coordinationScore: number;
    }>();

    data.forEach(game => {
      const modelName = Object.values(game.model_config || {})[0] || 'Unknown';

      if (!modelMap.has(modelName)) {
        modelMap.set(modelName, {
          totalGames: 0,
          successfulGames: 0,
          totalRounds: 0,
          totalTime: 0,
          avgDecisionTime: 0,
          coordinationScore: 0
        });
      }

      const stats = modelMap.get(modelName)!;
      stats.totalGames++;
      if (game.final_success) stats.successfulGames++;
      stats.totalRounds += game.round_number;
      stats.totalTime += game.time_taken;

      // Calculate coordination score based on action data
      if (game.action_data && game.action_data.length > 0) {
        const correctActions = game.action_data.filter(a => a.correct !== false).length;
        const totalActions = game.action_data.length;
        stats.coordinationScore += (correctActions / totalActions) * 100;
      }
    });

    return Array.from(modelMap.entries()).map(([name, stats]) => ({
      name,
      successRate: (stats.successfulGames / stats.totalGames) * 100,
      avgRounds: stats.totalRounds / stats.totalGames,
      avgTime: stats.totalTime / stats.totalGames,
      coordinationScore: stats.coordinationScore / stats.totalGames,
      totalGames: stats.totalGames
    }));
  };

  const modelStats = getModelStats();

  // Prepare radar chart data
  const radarData = modelStats.map(model => ({
    model: model.name,
    'Success Rate': model.successRate,
    'Avg Rounds': (model.avgRounds / 10) * 100, // Normalize to 0-100
    'Coordination': model.coordinationScore,
    'Speed': Math.max(0, 100 - (model.avgTime / 30) * 100) // Inverse time, normalized
  }));

  // Prepare scatter plot data
  const scatterData = modelStats.map(model => ({
    name: model.name,
    x: model.avgTime,
    y: model.successRate,
    z: model.totalGames
  }));

  const COLORS = ['#8b5cf6', '#3b82f6', '#14b8a6', '#f59e0b', '#ec4899', '#22c55e'];

  return (
    <div className="model-comparison">
      <h2>Model Performance Comparison</h2>

      <div className="comparison-grid">
        <div className="comparison-card full-width">
          <h3>Multi-Dimensional Performance Analysis</h3>
          <ResponsiveContainer width="100%" height={400}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="#cbd5e1" />
              <PolarAngleAxis
                dataKey="model"
                tick={{ fill: '#475569', fontSize: 12 }}
              />
              <PolarRadiusAxis
                angle={90}
                domain={[0, 100]}
                tick={{ fill: '#475569' }}
              />
              <Radar
                name="Performance Metrics"
                dataKey="Success Rate"
                stroke="#4f46e5"
                fill="#4f46e5"
                fillOpacity={0.6}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #cbd5e1',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                }}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        <div className="comparison-card">
          <h3>Success Rate vs. Decision Speed</h3>
          <ResponsiveContainer width="100%" height={300}>
            <ScatterChart>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis
                type="number"
                dataKey="x"
                name="Avg Time (s)"
                tick={{ fill: '#475569' }}
                label={{ value: 'Average Time (seconds)', position: 'bottom', style: { fill: '#475569' } }}
              />
              <YAxis
                type="number"
                dataKey="y"
                name="Success Rate (%)"
                tick={{ fill: '#475569' }}
                label={{ value: 'Success Rate (%)', angle: -90, position: 'insideLeft', style: { fill: '#475569' } }}
              />
              <Tooltip
                cursor={{ strokeDasharray: '3 3' }}
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #cbd5e1',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                }}
                formatter={(value: any, name: string) => {
                  if (name === 'x') return [`${value.toFixed(2)}s`, 'Avg Time'];
                  if (name === 'y') return [`${value.toFixed(1)}%`, 'Success Rate'];
                  if (name === 'z') return [`${value} games`, 'Total Games'];
                  return value;
                }}
              />
              <Scatter name="Models" data={scatterData}>
                {scatterData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
        </div>

        <div className="comparison-card">
          <h3>Model Statistics</h3>
          <div className="model-stats-list">
            {modelStats.map((model, index) => (
              <div key={index} className="model-stat-card">
                <div className="model-stat-header">
                  <div
                    className="model-color-indicator"
                    style={{ backgroundColor: COLORS[index % COLORS.length] }}
                  />
                  <h4>{model.name}</h4>
                </div>
                <div className="model-stat-metrics">
                  <div className="stat-row">
                    <span className="stat-label">Success Rate</span>
                    <span className="stat-value">{model.successRate.toFixed(1)}%</span>
                  </div>
                  <div className="stat-row">
                    <span className="stat-label">Avg Rounds</span>
                    <span className="stat-value">{model.avgRounds.toFixed(2)}</span>
                  </div>
                  <div className="stat-row">
                    <span className="stat-label">Avg Time</span>
                    <span className="stat-value">{model.avgTime.toFixed(2)}s</span>
                  </div>
                  <div className="stat-row">
                    <span className="stat-label">Coordination Score</span>
                    <span className="stat-value">{model.coordinationScore.toFixed(1)}%</span>
                  </div>
                  <div className="stat-row">
                    <span className="stat-label">Total Games</span>
                    <span className="stat-value">{model.totalGames}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ModelComparison;
