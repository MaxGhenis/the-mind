import React from 'react';
import { ActionData } from '../types';

interface LLMReasoningPanelProps {
  actionData?: ActionData[];
  roundNumber: number;
}

const LLMReasoningPanel: React.FC<LLMReasoningPanelProps> = ({ actionData, roundNumber }) => {
  if (!actionData || actionData.length === 0) {
    return (
      <div className="llm-reasoning-panel">
        <h3>LLM Reasoning</h3>
        <p className="no-data">No reasoning data available for this round.</p>
      </div>
    );
  }

  return (
    <div className="llm-reasoning-panel">
      <h3>LLM Decision Timeline</h3>
      <div className="reasoning-timeline">
        {actionData.map((action, index) => (
          <div
            key={action.action_id}
            className={`reasoning-card ${action.correct === false ? 'error' : ''}`}
          >
            <div className="reasoning-header">
              <div className="player-badge">Player {action.player}</div>
              <div className="card-value">Card: {action.card}</div>
              {action.correct === false && (
                <div className="error-badge">ERROR</div>
              )}
            </div>

            <div className="reasoning-metrics">
              <div className="metric">
                <span className="metric-label">Decision Time</span>
                <span className="metric-value">{action.decision_time.toFixed(2)}s</span>
              </div>
              <div className="metric">
                <span className="metric-label">Wait Time</span>
                <span className="metric-value">{action.wait_time.toFixed(2)}s</span>
              </div>
              {action.play_time !== null && (
                <div className="metric">
                  <span className="metric-label">Play Time</span>
                  <span className="metric-value">{action.play_time.toFixed(2)}s</span>
                </div>
              )}
              {action.llm_response_time !== null && (
                <div className="metric">
                  <span className="metric-label">LLM Response</span>
                  <span className="metric-value">{action.llm_response_time.toFixed(2)}s</span>
                </div>
              )}
            </div>

            {action.correct === false && action.should_have_been && (
              <div className="error-explanation">
                <strong>Coordination Failure:</strong> Should have played {action.should_have_been} instead
              </div>
            )}

            {action.error && (
              <div className="error-message">
                <strong>Error:</strong> {action.error}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default LLMReasoningPanel;
