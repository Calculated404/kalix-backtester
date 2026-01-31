import './TradesTable.css';

export default function TradesTable({ trades = [], strategyName = '', metrics = {} }) {
  if (!trades || trades.length === 0) {
    return null;
  }

  return (
    <div className="trades-table-container">
      <div className="trades-header-row">
        <h3>Trade History - {strategyName.replace(/_/g, ' ')}</h3>
        <div className="trades-count-badge">
          📊 {trades.length} Trade{trades.length !== 1 ? 's' : ''}
        </div>
      </div>

      {metrics && Object.keys(metrics).length > 0 && (
        <div className="metrics-header">
          <div className="metric-card">
            <span className="label">Initial Cash</span>
            <span className="value">${metrics.start_cash?.toLocaleString()}</span>
          </div>
          <div className="metric-card">
            <span className="label">Final Equity</span>
            <span className="value">${metrics.final_equity?.toLocaleString()}</span>
          </div>
          <div className="metric-card">
            <span className="label">Net Profit</span>
            <span className={`value ${metrics.net_profit >= 0 ? 'green' : 'red'}`}>
              {metrics.net_profit >= 0 ? '+' : ''}${metrics.net_profit?.toLocaleString()}
            </span>
          </div>
          <div className="metric-card">
            <span className="label">Total Return</span>
            <span className={`value ${metrics.total_return_pct >= 0 ? 'green' : 'red'}`}>
              {metrics.total_return_pct}%
            </span>
          </div>
        </div>
      )}
      <div className="trades-table-wrapper">
        <table className="trades-table-detailed">
          <thead>
            <tr>
              <th>#</th>
              <th>Entry Date</th>
              <th>Entry Time</th>
              <th>Entry Price</th>
              <th>Exit Date</th>
              <th>Exit Time</th>
              <th>Exit Price</th>
              <th>P&L</th>
              <th>Return %</th>
            </tr>
          </thead>
          <tbody>
            {trades.map((trade, idx) => {
              const entryDate = trade.entry_time ? new Date(trade.entry_time) : null;
              const exitDate = trade.exit_time ? new Date(trade.exit_time) : null;
              const isProfitable = trade.pnl >= 0;

              return (
                <tr key={idx} className={isProfitable ? 'profit' : 'loss'}>
                  <td>{idx + 1}</td>
                  <td>{entryDate ? entryDate.toLocaleDateString() : '-'}</td>
                  <td>{entryDate ? entryDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '-'}</td>
                  <td>{trade.entry_price ? trade.entry_price.toFixed(5) : '-'}</td>
                  <td>{exitDate ? exitDate.toLocaleDateString() : 'Open'}</td>
                  <td>{exitDate ? exitDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '-'}</td>
                  <td>{trade.exit_price ? trade.exit_price.toFixed(5) : '-'}</td>
                  <td className={isProfitable ? 'green' : 'red'}>
                    {isProfitable ? '+' : ''}{trade.pnl ? trade.pnl.toFixed(2) : '0.00'}
                  </td>
                  <td className={isProfitable ? 'green' : 'red'}>
                    {isProfitable ? '+' : ''}{trade.return_pct ? (trade.return_pct * 100).toFixed(2) : '0.00'}%
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
