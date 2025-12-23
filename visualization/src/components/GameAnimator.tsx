import React, { useState, useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { GameData } from '../types';
import LLMReasoningPanel from './LLMReasoningPanel';

interface GameAnimatorProps {
  data: GameData[];
}

const GameAnimator: React.FC<GameAnimatorProps> = ({ data }) => {
  const [selectedGame, setSelectedGame] = useState<string | null>(null);
  const [selectedRound, setSelectedRound] = useState<number>(1);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [currentTime, setCurrentTime] = useState(0);
  const [omniscientMode, setOmniscientMode] = useState(false);
  const animationRef = useRef<number | null>(null);
  const startTimeRef = useRef<number>(0);

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

  const handlePlay = () => {
    if (!roundData) return;
    
    if (isPlaying) {
      setIsPlaying(false);
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    } else {
      setIsPlaying(true);
      setCurrentTime(0);
      startTimeRef.current = performance.now();
      animate();
    }
  };

  const animate = () => {
    if (!roundData) return;
    
    const elapsed = (performance.now() - startTimeRef.current) / 1000 * playbackSpeed;
    setCurrentTime(elapsed);
    
    // Parse cards and find error point
    const cards = roundData.cards_played || [];
    const cardValues = Array.isArray(cards) ? cards : [];
    
    // Use real timing data if available, otherwise fall back to interpolation
    let cardData;
    if (roundData.action_data && roundData.action_data.length > 0) {
      // Use real timing from action_data
      const playedActions = roundData.action_data
        .filter(a => a.play_time !== null)
        .sort((a, b) => (a.play_time || 0) - (b.play_time || 0));
      
      cardData = playedActions.map((action, index) => ({
        value: action.card,
        time: action.play_time || 0,
        index,
        player: action.player
      }));
    } else {
      // Fall back to equal time division (old behavior)
      cardData = cardValues.map((value: any, index: number) => ({
        value: typeof value === 'number' ? value : parseInt(value),
        time: (index + 1) * (roundData.time_taken / Math.max(cardValues.length, 1)),
        index,
        player: (index % roundData.num_players) + 1
      }));
    }

    // Find first error (if any)
    let errorTime = roundData.time_taken;
    if (roundData.action_data && roundData.action_data.length > 0) {
      // Use action_data to find error point
      const firstError = roundData.action_data.find(a => a.correct === false);
      if (firstError && firstError.play_time !== null) {
        errorTime = firstError.play_time;
      }
    } else {
      // Fall back to checking sorted order
      const sortedCards = [...cardValues].sort((a, b) => a - b);
      for (let i = 0; i < cardValues.length; i++) {
        if (cardValues[i] !== sortedCards[i]) {
          errorTime = cardData[i].time;
          break;
        }
      }
    }
    
    if (elapsed < errorTime) {
      animationRef.current = requestAnimationFrame(animate);
    } else {
      setIsPlaying(false);
      setCurrentTime(errorTime);
    }
  };

  useEffect(() => {
    if (!isPlaying && animationRef.current) {
      cancelAnimationFrame(animationRef.current);
    }
  }, [isPlaying]);

  useEffect(() => {
    if (!roundData) return;

    // Clear previous visualization
    d3.select('#game-animator').selectAll('*').remove();

    const width = 900;
    const height = 500;
    const margin = { top: 40, right: 30, bottom: 60, left: 60 };

    const svg = d3.select('#game-animator')
      .append('svg')
      .attr('width', width)
      .attr('height', height);

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    // Create scales
    const xScale = d3.scaleLinear()
      .domain([0, roundData.time_taken || 30])
      .range([0, innerWidth]);

    const yScale = d3.scaleLinear()
      .domain([0, 100])
      .range([innerHeight, 0]);

    // Add axes
    g.append('g')
      .attr('transform', `translate(0,${innerHeight})`)
      .call(d3.axisBottom(xScale))
      .append('text')
      .attr('x', innerWidth / 2)
      .attr('y', 40)
      .attr('fill', 'black')
      .style('text-anchor', 'middle')
      .style('font-size', '14px')
      .text('Time (seconds)');

    g.append('g')
      .call(d3.axisLeft(yScale))
      .append('text')
      .attr('transform', 'rotate(-90)')
      .attr('y', -40)
      .attr('x', -innerHeight / 2)
      .attr('fill', 'black')
      .style('text-anchor', 'middle')
      .style('font-size', '14px')
      .text('Card Value');

    // Add title
    svg.append('text')
      .attr('x', width / 2)
      .attr('y', 20)
      .style('text-anchor', 'middle')
      .style('font-size', '18px')
      .style('font-weight', 'bold')
      .text(`Round ${selectedRound} - ${roundData.success ? 'Success' : 'Failed'}`);

    // Parse cards and create timeline data
    const cards = roundData.cards_played || [];
    const cardValues = Array.isArray(cards) ? cards : [];
    
    // Use real timing data if available, otherwise fall back to interpolation
    let cardData;
    if (roundData.action_data && roundData.action_data.length > 0) {
      // Use real timing from action_data
      const playedActions = roundData.action_data
        .filter(a => a.play_time !== null)
        .sort((a, b) => (a.play_time || 0) - (b.play_time || 0));
      
      cardData = playedActions.map((action, index) => ({
        value: action.card,
        time: action.play_time || 0,
        index,
        player: action.player
      }));
    } else {
      // Fall back to equal time division (old behavior)
      cardData = cardValues.map((value: any, index: number) => ({
        value: typeof value === 'number' ? value : parseInt(value),
        time: (index + 1) * (roundData.time_taken / Math.max(cardValues.length, 1)),
        index,
        player: (index % roundData.num_players) + 1
      }));
    }

    // Find first error point
    let errorIndex = -1;
    if (roundData.action_data && roundData.action_data.length > 0) {
      // Use action_data to find error point
      const playedActions = roundData.action_data
        .filter(a => a.play_time !== null)
        .sort((a, b) => (a.play_time || 0) - (b.play_time || 0));
      
      errorIndex = playedActions.findIndex(a => a.correct === false);
    } else {
      // Fall back to checking sorted order
      const sortedCards = [...cardValues].sort((a, b) => a - b);
      for (let i = 0; i < cardValues.length; i++) {
        if (cardValues[i] !== sortedCards[i]) {
          errorIndex = i;
          break;
        }
      }
    }

    // Player colors
    const playerColors = d3.scaleOrdinal(d3.schemeCategory10);
    
    // In omniscient mode, show all cards from the start as gray outlines
    if (omniscientMode) {
      g.selectAll('.omniscient-card')
        .data(cardData)
        .enter().append('circle')
        .attr('class', 'omniscient-card')
        .attr('cx', d => xScale(d.time))
        .attr('cy', d => yScale(d.value))
        .attr('r', 6)
        .attr('fill', 'none')
        .attr('stroke', '#ccc')
        .attr('stroke-width', 1)
        .style('opacity', 0.3);
      
      g.selectAll('.omniscient-label')
        .data(cardData)
        .enter().append('text')
        .attr('class', 'omniscient-label')
        .attr('x', d => xScale(d.time))
        .attr('y', d => yScale(d.value) - 12)
        .style('text-anchor', 'middle')
        .style('font-size', '10px')
        .style('fill', '#999')
        .style('opacity', 0.5)
        .text(d => d.value);
    }

    // Draw current time indicator
    g.append('line')
      .attr('class', 'time-indicator')
      .attr('x1', xScale(currentTime))
      .attr('x2', xScale(currentTime))
      .attr('y1', 0)
      .attr('y2', innerHeight)
      .attr('stroke', '#ff6b6b')
      .attr('stroke-width', 2)
      .attr('stroke-dasharray', '5,5');

    // Determine which cards to show based on current time and error
    let visibleCards: any[] = [];
    let futureCards: any[] = [];
    
    if (errorIndex >= 0) {
      // There's an error - stop at the error point
      const errorTime = cardData[errorIndex].time;
      visibleCards = cardData.filter(d => d.time <= Math.min(currentTime, errorTime));
      
      // Show future cards as dashed lines if we're at the error point
      if (currentTime >= errorTime) {
        futureCards = cardData.filter(d => d.time > errorTime);
        
        // Draw vertical dashed line at error time
        g.append('line')
          .attr('x1', xScale(errorTime))
          .attr('x2', xScale(errorTime))
          .attr('y1', 0)
          .attr('y2', innerHeight)
          .attr('stroke', '#f44336')
          .attr('stroke-width', 2)
          .attr('stroke-dasharray', '10,5')
          .style('opacity', 0.8);
      }
    } else {
      // No error - show cards up to current time
      visibleCards = cardData.filter(d => d.time <= currentTime);
    }
    
    // Draw lines for played cards
    if (visibleCards.length > 1) {
      const line = d3.line<any>()
        .x(d => xScale(d.time))
        .y(d => yScale(d.value));

      g.append('path')
        .datum(visibleCards)
        .attr('fill', 'none')
        .attr('stroke', errorIndex >= 0 ? '#f44336' : '#4CAF50')
        .attr('stroke-width', 2)
        .attr('opacity', 0.6)
        .attr('d', line);
    }

    // Draw played cards as circles
    g.selectAll('.card')
      .data(visibleCards)
      .enter().append('circle')
      .attr('class', 'card')
      .attr('cx', d => xScale(d.time))
      .attr('cy', d => yScale(d.value))
      .attr('r', 8)
      .attr('fill', d => playerColors(d.player.toString()))
      .attr('stroke', 'white')
      .attr('stroke-width', 2)
      .on('mouseover', function(event, d) {
        // Show tooltip
        const tooltip = d3.select('body').append('div')
          .attr('class', 'tooltip')
          .style('position', 'absolute')
          .style('background', 'rgba(0, 0, 0, 0.8)')
          .style('color', 'white')
          .style('padding', '8px 12px')
          .style('border-radius', '4px')
          .style('pointer-events', 'none')
          .style('opacity', 0);

        tooltip.transition()
          .duration(200)
          .style('opacity', 0.9);

        const isError = errorIndex >= 0 && d.index === errorIndex;
        
        let tooltipText = `Player ${d.player}<br/>Card: ${d.value}<br/>Time: ${d.time.toFixed(1)}s`;
        
        // Add error information if available from action_data
        if (roundData.action_data && roundData.action_data.length > 0) {
          const action = roundData.action_data.find(a => a.card === d.value);
          if (action && action.correct === false && action.should_have_been) {
            tooltipText += `<br/><span style="color: #ff6b6b">Should have been: ${action.should_have_been}</span>`;
          }
        } else if (isError) {
          // Fall back to calculating expected card
          const sortedCards = [...cardValues].sort((a, b) => a - b);
          const expectedCard = sortedCards[d.index];
          tooltipText += `<br/><span style="color: #ff6b6b">Should have been: ${expectedCard}</span>`;
        }
        
        tooltip.html(tooltipText)
          .style('left', (event.pageX + 10) + 'px')
          .style('top', (event.pageY - 28) + 'px');
      })
      .on('mouseout', function() {
        d3.selectAll('.tooltip').remove();
      });

    // Add card value labels for played cards
    g.selectAll('.card-label')
      .data(visibleCards)
      .enter().append('text')
      .attr('class', 'card-label')
      .attr('x', d => xScale(d.time))
      .attr('y', d => yScale(d.value) - 12)
      .style('text-anchor', 'middle')
      .style('font-size', '12px')
      .style('font-weight', 'bold')
      .text(d => d.value);

    // Draw future cards (what would have happened)
    if (futureCards.length > 0) {
      // Draw dashed lines to future cards
      futureCards.forEach(card => {
        g.append('line')
          .attr('x1', xScale(card.time))
          .attr('x2', xScale(card.time))
          .attr('y1', yScale(0))
          .attr('y2', yScale(card.value))
          .attr('stroke', playerColors(card.player.toString()))
          .attr('stroke-width', 1)
          .attr('stroke-dasharray', '5,3')
          .style('opacity', 0.4);
      });

      // Draw future cards as hollow circles
      g.selectAll('.future-card')
        .data(futureCards)
        .enter().append('circle')
        .attr('class', 'future-card')
        .attr('cx', d => xScale(d.time))
        .attr('cy', d => yScale(d.value))
        .attr('r', 6)
        .attr('fill', 'none')
        .attr('stroke', d => playerColors(d.player.toString()))
        .attr('stroke-width', 2)
        .style('opacity', 0.5)
        .attr('stroke-dasharray', '3,2');

      // Add labels for future cards
      g.selectAll('.future-label')
        .data(futureCards)
        .enter().append('text')
        .attr('class', 'future-label')
        .attr('x', d => xScale(d.time))
        .attr('y', d => yScale(d.value) - 12)
        .style('text-anchor', 'middle')
        .style('font-size', '11px')
        .style('opacity', 0.6)
        .style('font-style', 'italic')
        .text(d => d.value);
    }

  }, [roundData, currentTime, selectedRound, omniscientMode]);

  return (
    <div className="game-animator">
      <h2>Game Animation</h2>
      
      <div className="controls">
        <div className="control-group">
          <label htmlFor="game-select">Select Game:</label>
          <select 
            id="game-select"
            value={selectedGame || ''}
            onChange={(e) => {
              setSelectedGame(e.target.value);
              setCurrentTime(0);
              setIsPlaying(false);
            }}
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
            onChange={(e) => {
              setSelectedRound(Number(e.target.value));
              setCurrentTime(0);
              setIsPlaying(false);
            }}
          >
            {rounds.map(round => (
              <option key={round} value={round}>
                Round {round}
              </option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label htmlFor="speed-control">Playback Speed:</label>
          <select
            id="speed-control"
            value={playbackSpeed}
            onChange={(e) => setPlaybackSpeed(Number(e.target.value))}
          >
            <option value={0.5}>0.5x</option>
            <option value={1}>1x</option>
            <option value={2}>2x</option>
            <option value={5}>5x</option>
            <option value={10}>10x</option>
          </select>
        </div>

        <div className="control-group">
          <button 
            onClick={handlePlay}
            className="btn btn-primary"
          >
            {isPlaying ? 'Pause' : 'Play'}
          </button>
          <button 
            onClick={() => {
              setCurrentTime(0);
              setIsPlaying(false);
            }}
            className="btn btn-secondary"
          >
            Reset
          </button>
        </div>

        <div className="control-group">
          <label>
            <input
              type="checkbox"
              checked={omniscientMode}
              onChange={(e) => setOmniscientMode(e.target.checked)}
              style={{ marginRight: '5px' }}
            />
            Omniscient Mode
          </label>
        </div>

        {roundData && (
          <div className="time-display">
            <span>Time: {currentTime.toFixed(1)}s / {roundData.time_taken.toFixed(1)}s</span>
          </div>
        )}
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
            <span className="label">Players:</span>
            <span className="value">{roundData.num_players}</span>
          </div>
          <div className="info-card">
            <span className="label">Experiment:</span>
            <span className="value">{roundData.experiment}</span>
          </div>
        </div>
      )}

      <div id="game-animator" className="visualization-container"></div>

      {roundData && Array.isArray(roundData.cards_played) && (
        <div className="card-sequence">
          <h3>Card Play Order</h3>
          <div className="sequence">
            {roundData.cards_played.map((card: any, index: number) => {
              const cardValue = typeof card === 'number' ? card : parseInt(card);
              const sortedCards = [...roundData.cards_played].sort((a, b) => a - b);
              const expectedValue = sortedCards[index];
              const isCorrect = cardValue === expectedValue;
              
              return (
                <span 
                  key={index} 
                  className={`card-badge ${!isCorrect ? 'error' : ''}`}
                  title={!isCorrect ? `Should be ${expectedValue}` : ''}
                >
                  {cardValue}
                  {!isCorrect && index === roundData.cards_played.findIndex((c: any, i: number) => c !== sortedCards[i]) && (
                    <span style={{ marginLeft: '4px' }}>❌</span>
                  )}
                </span>
              );
            })}
          </div>
          {!roundData.success && (
            <p style={{ marginTop: '10px', color: '#f44336', fontSize: '14px' }}>
              Game failed when Player {(roundData.cards_played.findIndex((c: any, i: number) => c !== [...roundData.cards_played].sort((a, b) => a - b)[i]) % roundData.num_players) + 1} played {
                roundData.cards_played[roundData.cards_played.findIndex((c: any, i: number) => c !== [...roundData.cards_played].sort((a, b) => a - b)[i])]
              } instead of {
                [...roundData.cards_played].sort((a, b) => a - b)[roundData.cards_played.findIndex((c: any, i: number) => c !== [...roundData.cards_played].sort((a, b) => a - b)[i])]
              }
            </p>
          )}
        </div>
      )}

      {roundData && (
        <LLMReasoningPanel
          actionData={roundData.action_data}
          roundNumber={selectedRound}
        />
      )}
    </div>
  );
};

export default GameAnimator;