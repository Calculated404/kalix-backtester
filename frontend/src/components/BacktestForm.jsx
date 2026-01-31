import { useState, useEffect } from 'react';
import './BacktestForm.css';

const PERIOD_OPTIONS = [1, 2, 3, 4, 5];
const MAX_ENTRIES_OPTIONS = [1, 2, 3, 4];

// Map timeframes to their maximum available periods
const TIMEFRAME_PERIOD_LIMITS = {
  '1m': 1,      // 1m: max 1 day (5 days fetched, used as max 1)
  '5m': 1,      // 5m: max 1 day
  '15m': 2,     // 15m: max ~60 days = 2 months approx
  '30m': 2,     // 30m: max ~60 days
  '1h': 2,      // 1h: max 2 years
  '4h': 2,      // 4h: max 2 years (via 1h resampling)
  '1d': 5,      // 1d: full history (5 years)
};

const TICKER_OPTIONS = [
  { label: 'EUR/CHF', value: 'EURCHF=X' },
  { label: 'GBP/USD', value: 'GBPUSD=X' },
  { label: 'AUD/USD', value: 'AUDUSD=X' },
  { label: 'XAU/USD (Gold)', value: 'GC=F' },
  { label: 'XAG/USD (Silver)', value: 'SI=F' },
  { label: 'NVIDIA', value: 'NVDA' },
  { label: 'Tesla', value: 'TSLA' },
  { label: 'Apple', value: 'AAPL' },
];

// Strategy display names
const STRATEGY_NAMES = {
  'trend_momentum_volume': 'Trend + Momentum + Volume (TMV)',
  'mean_reversion': 'Mean Reversion',
  'trend_following': 'Trend Following',
  'double_rsi': 'Double RSI'
};

const VALID_INTERVALS = [
  { label: '1 Minute (last 5 days)', value: '1m' },
  { label: '15 Minutes (last 60 days)', value: '15m' },
  { label: '1 Hour (last 2 years)', value: '1h' },
  { label: '4 Hours (last 2 years)', value: '4h' },
  { label: '1 Day (full history)', value: '1d' },
];

export default function BacktestForm({
  strategies = [],
  periodYears,
  onPeriodChange,
  ticker,
  onTickerChange,
  interval,
  onIntervalChange,
  onRun,
  loading,
}) {
  const [initialCash, setInitialCash] = useState(10000);
  const [commission, setCommission] = useState(0.00005);
  const [selectedStrategies, setSelectedStrategies] = useState(
    strategies.length ? [strategies.includes('trend_momentum_volume') ? 'trend_momentum_volume' : strategies[0]] : ['trend_momentum_volume']
  );
  const [maxEntriesPerWeek, setMaxEntriesPerWeek] = useState(2);
  const [cooldownDays, setCooldownDays] = useState(2);

  // Adjust period when interval changes
  useEffect(() => {
    const maxPeriodForInterval = TIMEFRAME_PERIOD_LIMITS[interval] || 5;
    if (periodYears > maxPeriodForInterval) {
      onPeriodChange(maxPeriodForInterval);
    }
  }, [interval, periodYears, onPeriodChange]);

  const toggleStrategy = (name) => {
    setSelectedStrategies((prev) =>
      prev.includes(name) ? prev.filter((s) => s !== name) : [...prev, name]
    );
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onRun({
      ticker,
      interval,
      periodYears,
      strategies: selectedStrategies.length ? selectedStrategies : ['trend_momentum_volume'],
      initialCash,
      commission,
      maxEntriesPerWeek,
      cooldownDays,
    });
  };

  return (
    <form className="backtest-form" onSubmit={handleSubmit}>
      <h2>Backtest settings</h2>

      <label>
        <span>Symbol (Forex / Stock)</span>
        <select
          value={ticker}
          onChange={(e) => onTickerChange(e.target.value)}
        >
          {TICKER_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </label>

      <label>
        <span>Timeframe</span>
        <select
          value={interval}
          onChange={(e) => onIntervalChange(e.target.value)}
        >
          {VALID_INTERVALS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </label>

      <label>
        <span>Amount to trade (initial cash)</span>
        <input
          type="number"
          min={100}
          step={100}
          value={initialCash}
          onChange={(e) => setInitialCash(Number(e.target.value))}
        />
      </label>

      <label>
        <span>Period (years) - Max available: {TIMEFRAME_PERIOD_LIMITS[interval]} year(s)</span>
        <select
          value={periodYears}
          onChange={(e) => onPeriodChange(Number(e.target.value))}
        >
          {PERIOD_OPTIONS.filter(y => y <= (TIMEFRAME_PERIOD_LIMITS[interval] || 5)).map((y) => (
            <option key={y} value={y}>
              {y} year{y > 1 ? 's' : ''}
            </option>
          ))}
        </select>
        {TIMEFRAME_PERIOD_LIMITS[interval] < 5 && (
          <small style={{ color: '#f59e0b', display: 'block', marginTop: '4px' }}>
            ⚠️ {interval} data limited to {TIMEFRAME_PERIOD_LIMITS[interval]} year(s) by data provider
          </small>
        )}
      </label>

      <fieldset>
        <span className="label">Strategy / signals</span>
        <div className="strategy-list">
          {strategies.length
            ? strategies.map((s) => (
                <label key={s} className="checkbox">
                  <input
                    type="checkbox"
                    checked={selectedStrategies.includes(s)}
                    onChange={() => toggleStrategy(s)}
                  />
                  {STRATEGY_NAMES[s] || s.replace(/_/g, ' ')}
                </label>
              ))
            : (
                <label className="checkbox">
                  <input
                    type="checkbox"
                    checked={selectedStrategies.includes('trend_momentum_volume')}
                    onChange={() => toggleStrategy('trend_momentum_volume')}
                  />
                  Trend + Momentum + Volume (TMV)
                </label>
              )}
        </div>
      </fieldset>

      <label>
        <span>Commission (spread + fees)</span>
        <input
          type="number"
          min={0}
          step={0.00001}
          value={commission}
          onChange={(e) => setCommission(Number(e.target.value))}
        />
      </label>

      <label>
        <span>Max entries per week (1–4)</span>
        <select
          value={maxEntriesPerWeek}
          onChange={(e) => setMaxEntriesPerWeek(Number(e.target.value))}
        >
          {MAX_ENTRIES_OPTIONS.map((n) => (
            <option key={n} value={n}>
              {n}
            </option>
          ))}
        </select>
      </label>

      <label>
        <span>Cooldown after close (days)</span>
        <input
          type="number"
          min={0}
          max={10}
          value={cooldownDays}
          onChange={(e) => setCooldownDays(Number(e.target.value))}
        />
      </label>

      <p style={{ fontSize: '0.8rem', color: '#a1a1aa', marginTop: '1rem' }}>
        📝 Note: Intraday data (1m, 15m) has limited historical availability from Yahoo Finance.
        For best results, use 1h or 1d timeframes for longer periods.
      </p>

      <button type="submit" disabled={loading}>
        {loading ? 'Running…' : 'Run backtest'}
      </button>
    </form>
  );
}
