import './ResultsPanel.css';

export default function ResultsPanel({ results = [] }) {
  return (
    <div className="results-panel">
      <h2>Results</h2>
      {results.map((r) => (
        <div key={r.strategy} className="result-block">
          <h3>{r.strategy.replace(/_/g, ' ')}</h3>
          {r.error && <div className="error">{r.error}</div>}
          {r.metrics && (
            <>
              <div className="metrics-summary">
                <div className="metric-card">
                  <span className="label">Initial Cash</span>
                  <span className="value">${r.metrics.start_cash?.toLocaleString()}</span>
                </div>
                <div className="metric-card">
                  <span className="label">Final Equity</span>
                  <span className="value">${r.metrics.final_equity?.toLocaleString()}</span>
                </div>
                <div className="metric-card">
                  <span className="label">Net Profit</span>
                  <span className={`value ${r.metrics.net_profit >= 0 ? 'green' : 'red'}`}>
                    {r.metrics.net_profit >= 0 ? '+' : ''}${r.metrics.net_profit?.toLocaleString()}
                  </span>
                </div>
                <div className="metric-card">
                  <span className="label">Total Return</span>
                  <span className={`value ${r.metrics.total_return_pct >= 0 ? 'green' : 'red'}`}>
                    {r.metrics.total_return_pct}%
                  </span>
                </div>
              </div>

              <table className="metrics-table">
                <tbody>
                  <tr><td>Win rate</td><td>{r.metrics.win_rate_pct}%</td></tr>
                  <tr><td>Max drawdown</td><td>{r.metrics.max_drawdown_pct}%</td></tr>
                  <tr><td># Trades</td><td>{r.metrics.num_trades}</td></tr>
                  <tr><td>Avg trades/week</td><td>{r.metrics.avg_trades_per_week}</td></tr>
                  <tr><td>Profit factor</td><td>{r.metrics.profit_factor}</td></tr>
                  <tr><td>Expectancy/trade</td><td>{r.metrics.expectancy_per_trade}</td></tr>
                </tbody>
              </table>

              {r.trades && r.trades.length > 0 && (
                <div className="trades-list">
                  <h4>Trades ({r.trades.length})</h4>
                  <table className="trades-table">
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Entry</th>
                        <th>Exit</th>
                        <th>PnL</th>
                      </tr>
                    </thead>
                    <tbody>
                      {r.trades.map((t, i) => (
                        <tr key={i}>
                          <td>
                            <div>{t.entry_time ? new Date(t.entry_time).toLocaleDateString() : '-'}</div>
                            <div className="price">{t.entry_time ? new Date(t.entry_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : ''}</div>
                          </td>
                          <td>
                            <div>{t.entry_price?.toFixed(4)}</div>
                          </td>
                          <td>
                            <div>{t.exit_price?.toFixed(4)}</div>
                            <div className="price">{t.exit_time ? new Date(t.exit_time).toLocaleDateString() : 'Open'}</div>
                          </td>
                          <td>
                            <div className={t.pnl >= 0 ? 'green' : 'red'}>
                              {t.pnl?.toFixed(2)}
                            </div>
                            <div className="pct">
                              {(t.return_pct * 100)?.toFixed(2)}%
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}
          {r.run_path && (
            <p className="run-path">
              Saved to <code>{r.run_path}</code>
            </p>
          )}
        </div>
      ))}
    </div>
  );
}
