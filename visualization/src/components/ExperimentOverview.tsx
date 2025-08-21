import React from 'react';
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell
} from 'recharts';
import { GameData, ExperimentSummary } from '../types';

interface ExperimentOverviewProps {
  data: GameData[];
}

const ExperimentOverview: React.FC<ExperimentOverviewProps> = ({ data }) => {
  // Process data into experiment summaries
  const getExperimentSummaries = (): ExperimentSummary[] => {
    const experiments = new Map<string, GameData[]>();
    
    data.forEach(row => {
      const key = row.experiment || 'default';
      if (!experiments.has(key)) {
        experiments.set(key, []);
      }
      experiments.get(key)!.push(row);
    });

    return Array.from(experiments.entries()).map(([name, games]) => {
      const uniqueGames = new Set(games.map(g => g.game_id));
      const successfulGames = new Set(
        games.filter(g => g.final_success).map(g => g.game_id)
      );
      
      const models = new Set<string>();
      games.forEach(g => {
        Object.values(g.model_config || {}).forEach(m => models.add(m));
      });

      return {
        name,
        totalGames: uniqueGames.size,
        successRate: successfulGames.size / uniqueGames.size,
        avgRounds: games.reduce((sum, g) => sum + g.round_number, 0) / games.length,
        avgTime: games.reduce((sum, g) => sum + g.time_taken, 0) / games.length,
        useMemory: games[0]?.use_memory || false,
        temperature: games[0]?.temperature || 0.7,
        models: Array.from(models)
      };
    });
  };

  const summaries = getExperimentSummaries();

  // Prepare data for charts
  const successRateData = summaries.map(s => ({
    name: s.name.replace(/_/g, ' '),
    'Success Rate': (s.successRate * 100).toFixed(1)
  }));

  const roundProgressData = summaries.map(s => ({
    name: s.name.replace(/_/g, ' '),
    'Avg Rounds': s.avgRounds.toFixed(1)
  }));

  const memoryComparison = summaries.reduce((acc, s) => {
    const key = s.useMemory ? 'With Memory' : 'No Memory';
    if (!acc[key]) {
      acc[key] = { count: 0, totalSuccess: 0 };
    }
    acc[key].count++;
    acc[key].totalSuccess += s.successRate;
    return acc;
  }, {} as Record<string, { count: number; totalSuccess: number }>);

  const memoryData = Object.entries(memoryComparison).map(([name, data]) => ({
    name,
    value: (data.totalSuccess / data.count * 100).toFixed(1)
  }));

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

  return (
    <div className="experiment-overview">
      <h2>Experiment Overview</h2>
      
      <div className="summary-stats">
        <div className="stat-card">
          <h3>Total Experiments</h3>
          <div className="stat-value">{summaries.length}</div>
        </div>
        <div className="stat-card">
          <h3>Total Games</h3>
          <div className="stat-value">
            {summaries.reduce((sum, s) => sum + s.totalGames, 0)}
          </div>
        </div>
        <div className="stat-card">
          <h3>Overall Success Rate</h3>
          <div className="stat-value">
            {(
              summaries.reduce((sum, s) => sum + s.successRate, 0) / 
              summaries.length * 100
            ).toFixed(1)}%
          </div>
        </div>
      </div>

      <div className="charts-grid">
        <div className="chart-container">
          <h3>Success Rate by Experiment</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={successRateData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
              <YAxis label={{ value: 'Success Rate (%)', angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Bar dataKey="Success Rate" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-container">
          <h3>Average Rounds Completed</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={roundProgressData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
              <YAxis label={{ value: 'Rounds', angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Line type="monotone" dataKey="Avg Rounds" stroke="#82ca9d" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-container">
          <h3>Memory Effect</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={memoryData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry) => `${entry.name}: ${entry.value}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {memoryData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="experiment-table">
        <h3>Detailed Results</h3>
        <table>
          <thead>
            <tr>
              <th>Experiment</th>
              <th>Games</th>
              <th>Success Rate</th>
              <th>Avg Rounds</th>
              <th>Avg Time (s)</th>
              <th>Memory</th>
              <th>Temperature</th>
              <th>Models</th>
            </tr>
          </thead>
          <tbody>
            {summaries.map((s, i) => (
              <tr key={i}>
                <td>{s.name}</td>
                <td>{s.totalGames}</td>
                <td>{(s.successRate * 100).toFixed(1)}%</td>
                <td>{s.avgRounds.toFixed(1)}</td>
                <td>{s.avgTime.toFixed(1)}</td>
                <td>{s.useMemory ? '✓' : '✗'}</td>
                <td>{s.temperature}</td>
                <td>{s.models.join(', ')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ExperimentOverview;