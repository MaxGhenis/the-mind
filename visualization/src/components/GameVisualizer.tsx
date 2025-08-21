import React, { useState, useEffect } from 'react';
import * as d3 from 'd3';
import { GameData } from '../types';

interface GameVisualizerProps {
  data: GameData[];
}

const GameVisualizer: React.FC<GameVisualizerProps> = ({ data }) => {
  const [selectedGame, setSelectedGame] = useState<string | null>(null);
  const [selectedRound, setSelectedRound] = useState<number>(1);

  // Get unique games
  const games = Array.from(new Set(data.map(d => d.game_id)));
  
  // Get data for selected game
  const gameData = selectedGame 
    ? data.filter(d => d.game_id === selectedGame)
    : [];
  
  const rounds = Array.from(new Set(gameData.map(d => d.round_number))).sort((a, b) => a - b);
  
  const roundData = gameData.find(d => d.round_number === selectedRound);

  useEffect(() => {
    if (games.length > 0 && !selectedGame) {
      setSelectedGame(games[0]);
    }
  }, [games, selectedGame]);

  useEffect(() => {
    if (!roundData) return;

    // Clear previous visualization
    d3.select('#game-viz').selectAll('*').remove();

    const width = 800;
    const height = 400;
    const margin = { top: 20, right: 30, bottom: 40, left: 50 };

    const svg = d3.select('#game-viz')
      .append('svg')
      .attr('width', width)
      .attr('height', height);

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    // Create scales
    const xScale = d3.scaleLinear()
      .domain([0, 100])
      .range([0, innerWidth]);

    const yScale = d3.scaleLinear()
      .domain([0, roundData.time_taken || 10])
      .range([innerHeight, 0]);

    // Add axes
    g.append('g')
      .attr('transform', `translate(0,${innerHeight})`)
      .call(d3.axisBottom(xScale))
      .append('text')
      .attr('x', innerWidth / 2)
      .attr('y', 35)
      .attr('fill', 'black')
      .style('text-anchor', 'middle')
      .text('Card Value');

    g.append('g')
      .call(d3.axisLeft(yScale))
      .append('text')
      .attr('transform', 'rotate(-90)')
      .attr('y', -35)
      .attr('x', -innerHeight / 2)
      .attr('fill', 'black')
      .style('text-anchor', 'middle')
      .text('Time (seconds)');

    // Add title
    svg.append('text')
      .attr('x', width / 2)
      .attr('y', 15)
      .style('text-anchor', 'middle')
      .style('font-size', '16px')
      .style('font-weight', 'bold')
      .text(`Round ${selectedRound} - ${roundData.success ? 'Success' : 'Failed'}`);

    // Plot cards
    const cards = roundData.cards_played || [];
    
    // Create timeline visualization
    const cardData = cards.map((value, index) => ({
      value,
      time: (index + 1) * (roundData.time_taken / cards.length),
      index
    }));

    // Draw lines connecting cards
    const line = d3.line<any>()
      .x(d => xScale(d.value))
      .y(d => yScale(d.time));

    g.append('path')
      .datum(cardData)
      .attr('fill', 'none')
      .attr('stroke', roundData.success ? '#4CAF50' : '#f44336')
      .attr('stroke-width', 2)
      .attr('d', line);

    // Draw cards as circles
    g.selectAll('.card')
      .data(cardData)
      .enter().append('circle')
      .attr('class', 'card')
      .attr('cx', d => xScale(d.value))
      .attr('cy', d => yScale(d.time))
      .attr('r', 6)
      .attr('fill', roundData.success ? '#4CAF50' : '#f44336')
      .attr('stroke', 'white')
      .attr('stroke-width', 2)
      .on('mouseover', function(event, d) {
        // Show tooltip
        const tooltip = d3.select('body').append('div')
          .attr('class', 'tooltip')
          .style('position', 'absolute')
          .style('background', 'rgba(0, 0, 0, 0.8)')
          .style('color', 'white')
          .style('padding', '5px 10px')
          .style('border-radius', '4px')
          .style('pointer-events', 'none')
          .style('opacity', 0);

        tooltip.transition()
          .duration(200)
          .style('opacity', 0.9);

        tooltip.html(`Card: ${d.value}<br/>Time: ${d.time.toFixed(1)}s<br/>Position: ${d.index + 1}`)
          .style('left', (event.pageX + 10) + 'px')
          .style('top', (event.pageY - 28) + 'px');
      })
      .on('mouseout', function() {
        d3.selectAll('.tooltip').remove();
      });

    // Add card value labels
    g.selectAll('.card-label')
      .data(cardData)
      .enter().append('text')
      .attr('class', 'card-label')
      .attr('x', d => xScale(d.value))
      .attr('y', d => yScale(d.time) - 10)
      .style('text-anchor', 'middle')
      .style('font-size', '12px')
      .text(d => d.value);

  }, [roundData]);

  return (
    <div className="game-visualizer">
      <h2>Game Visualization</h2>
      
      <div className="controls">
        <div className="control-group">
          <label htmlFor="game-select">Select Game:</label>
          <select 
            id="game-select"
            value={selectedGame || ''}
            onChange={(e) => setSelectedGame(e.target.value)}
          >
            {games.map(gameId => (
              <option key={gameId} value={gameId}>
                {gameId.substring(0, 8)}...
              </option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label htmlFor="round-select">Select Round:</label>
          <select 
            id="round-select"
            value={selectedRound}
            onChange={(e) => setSelectedRound(Number(e.target.value))}
          >
            {rounds.map(round => (
              <option key={round} value={round}>
                Round {round}
              </option>
            ))}
          </select>
        </div>
      </div>

      {roundData && (
        <div className="round-info">
          <div className="info-card">
            <span className="label">Status:</span>
            <span className={`value ${roundData.success ? 'success' : 'failure'}`}>
              {roundData.success ? 'Success' : 'Failed'}
            </span>
          </div>
          <div className="info-card">
            <span className="label">Cards Played:</span>
            <span className="value">{roundData.cards_played?.length || 0}</span>
          </div>
          <div className="info-card">
            <span className="label">Time Taken:</span>
            <span className="value">{roundData.time_taken?.toFixed(1)}s</span>
          </div>
          <div className="info-card">
            <span className="label">Players:</span>
            <span className="value">{roundData.num_players}</span>
          </div>
        </div>
      )}

      <div id="game-viz" className="visualization-container"></div>

      {roundData && (
        <div className="card-sequence">
          <h3>Card Sequence</h3>
          <div className="sequence">
            {roundData.cards_played?.map((card, index) => (
              <span key={index} className="card-badge">
                {card}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default GameVisualizer;