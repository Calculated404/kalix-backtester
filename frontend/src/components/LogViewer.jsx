import { useState, useEffect, useRef } from 'react';
import { appLogger, chartLogger, apiLogger, strategyLogger } from '../utils/logger';
import './LogViewer.css';

export default function LogViewer() {
  const [isOpen, setIsOpen] = useState(false);
  const [logs, setLogs] = useState([]);
  const [autoScroll, setAutoScroll] = useState(true);
  const [filterLevel, setFilterLevel] = useState(null);
  const logsEndRef = useRef(null);

  useEffect(() => {
    // Update logs every 500ms
    const interval = setInterval(() => {
      const allLogs = [
        ...appLogger.getLogs(),
        ...chartLogger.getLogs(),
        ...apiLogger.getLogs(),
        ...strategyLogger.getLogs(),
      ].sort((a, b) => a.timestamp - b.timestamp);

      if (filterLevel) {
        setLogs(allLogs.filter(log => log.level === filterLevel));
      } else {
        setLogs(allLogs);
      }
    }, 500);

    return () => clearInterval(interval);
  }, [filterLevel]);

  useEffect(() => {
    if (autoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll]);

  const getLevelColor = (level) => {
    const colors = {
      error: '#ff6b6b',
      warn: '#ffa94d',
      info: '#4ecdc4',
      debug: '#95e1d3',
      trace: '#a8e6cf',
    };
    return colors[level] || '#000';
  };

  return (
    <div className="log-viewer">
      <button
        className="log-toggle-btn"
        onClick={() => setIsOpen(!isOpen)}
        title="Toggle logs"
      >
        📋 Logs ({logs.length})
      </button>

      {isOpen && (
        <div className="log-panel">
          <div className="log-header">
            <h3>System Logs</h3>
            <div className="log-controls">
              <label>
                <input
                  type="checkbox"
                  checked={autoScroll}
                  onChange={(e) => setAutoScroll(e.target.checked)}
                />
                Auto-scroll
              </label>

              <select
                value={filterLevel || ''}
                onChange={(e) => setFilterLevel(e.target.value || null)}
                className="log-filter"
              >
                <option value="">All Levels</option>
                <option value="error">Errors</option>
                <option value="warn">Warnings</option>
                <option value="info">Info</option>
                <option value="debug">Debug</option>
                <option value="trace">Trace</option>
              </select>

              <button
                onClick={() => {
                  appLogger.clearLogs();
                  chartLogger.clearLogs();
                  apiLogger.clearLogs();
                  strategyLogger.clearLogs();
                  setLogs([]);
                }}
                className="log-clear-btn"
              >
                Clear
              </button>

              <button
                onClick={() => appLogger.downloadLogs()}
                className="log-download-btn"
              >
                Download
              </button>

              <button
                onClick={() => setIsOpen(false)}
                className="log-close-btn"
              >
                ✕
              </button>
            </div>
          </div>

          <div className="log-content">
            {logs.length === 0 ? (
              <div className="log-empty">No logs to display</div>
            ) : (
              logs.map((log, idx) => (
                <div
                  key={idx}
                  className="log-entry"
                  style={{ borderLeftColor: getLevelColor(log.level) }}
                >
                  <div className="log-time">{log.prefix}</div>
                  <div className="log-message">{log.message}</div>
                  {log.data && (
                    <div className="log-data">
                      {typeof log.data === 'object' ? JSON.stringify(log.data, null, 2) : String(log.data)}
                    </div>
                  )}
                </div>
              ))
            )}
            <div ref={logsEndRef} />
          </div>

          <div className="log-stats">
            <span>Total: {logs.length}</span>
            <span>Errors: {logs.filter(l => l.level === 'error').length}</span>
            <span>Warnings: {logs.filter(l => l.level === 'warn').length}</span>
          </div>
        </div>
      )}
    </div>
  );
}
