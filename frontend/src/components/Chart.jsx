import { useEffect, useRef, useState } from 'react';
import { createChart } from 'lightweight-charts';
import './Chart.css';

function parseTime(t) {
  if (!t) return null;
  const s = String(t);

  // If strictly yyyy-mm-dd, return as string (Daily)
  if (s.length === 10 && /^\d{4}-\d{2}-\d{2}$/.test(s)) {
    return s;
  }

  // Otherwise parse as Date and return Unix timestamp (Intraday)
  const d = new Date(t);
  if (isNaN(d.getTime())) return null;
  return Math.floor(d.getTime() / 1000);
}

export default function Chart({ data = [], markers = [], indicators = {}, height = 400, runResults = null }) {
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);
  const seriesRef = useRef({});
  const [chartError, setChartError] = useState(null);

  useEffect(() => {
    setChartError(null);

    if (!chartContainerRef.current) return;
    if (!data || data.length === 0) return;

    let chart;
    try {
      const containerWidth = chartContainerRef.current.clientWidth;
      if (containerWidth <= 0 || height <= 0) return;

      chart = createChart(chartContainerRef.current, {
        layout: { background: { color: '#18181b' }, textColor: '#a1a1aa' },
        grid: { vertLines: { color: '#27272a' }, horzLines: { color: '#27272a' } },
        width: containerWidth,
        height,
        timeScale: { timeVisible: true, secondsVisible: false },
        rightPriceScale: { borderColor: '#27272a' },
      });
      chartRef.current = chart;
      seriesRef.current = {};

      const candleSeries = chart.addCandlestickSeries({
        upColor: '#22c55e',
        downColor: '#ef4444',
        borderVisible: false,
        wickVisible: true,
        priceFormat: {
          type: 'price',
          precision: 3,
          minMove: 0.001,
        },
      });
      seriesRef.current.candles = candleSeries;

      // Parse and format data
      let ohlc = data.map((d) => {
        const time = parseTime(d.time) || parseTime(d.Date) || parseTime(d.datetime);
        if (!time) return null;

        return {
          time: time,
          open: Number(d.Open ?? d.open ?? 0),
          high: Number(d.High ?? d.high ?? 0),
          low: Number(d.Low ?? d.low ?? 0),
          close: Number(d.Close ?? d.close ?? 0),
        };
      }).filter(d => d !== null);

      // Sort by time
      ohlc.sort((a, b) => (a.time > b.time ? 1 : (a.time < b.time ? -1 : 0)));

      // Deduplicate by time
      const uniqueOhlc = [];
      const seenTimes = new Set();
      for (const item of ohlc) {
        if (!seenTimes.has(item.time)) {
          seenTimes.add(item.time);
          uniqueOhlc.push(item);
        }
      }
      ohlc = uniqueOhlc;

      if (ohlc.length === 0) {
        throw new Error("No valid price data available");
      }

      candleSeries.setData(ohlc);

      // Process markers
      let seriesMarkers = markers.map((m) => ({
        time: parseTime(m.time) || m.time,
        position: m.type === 'buy' ? 'belowBar' : 'aboveBar',
        color: m.type === 'buy' ? '#22c55e' : '#ef4444',
        shape: 'circle',
        text: (m.type === 'buy' ? 'B' : 'S') + (m.strategy ? ` ${m.strategy.substring(0, 2).toUpperCase()}` : ''),
      })).filter((m) => m.time);

      // Sort markers
      seriesMarkers.sort((a, b) => (a.time > b.time ? 1 : (a.time < b.time ? -1 : 0)));

      // Filter markers to ensure they match existing data times (optional but safer)
      // Actually lightweight-charts just ignores them if out of range, but duplicates in markers are allowed (stacked)
      // But markers must be sorted.

      if (seriesMarkers.length) {
        candleSeries.setMarkers(seriesMarkers);
      }

      chart.timeScale().fitContent();

      const handleResize = () => {
        if (chartContainerRef.current && chartRef.current) {
          chartRef.current.applyOptions({ width: chartContainerRef.current.clientWidth });
        }
      };
      window.addEventListener('resize', handleResize);

      return () => {
        window.removeEventListener('resize', handleResize);
        chart.remove();
        chartRef.current = null;
        seriesRef.current = {};
      };
    } catch (e) {
      console.error("Failed to create chart:", e);
      setChartError(e.message);
      if (chart) {
        chart.remove();
        chartRef.current = null;
      }
    }
  }, [data, markers, indicators, height]); // Removed runResults from dependency to avoid unnecessary re-renders

  // ... (rest of the component remains similar, just simplified)

  // Helper for strategy info
  const getStrategyFromIndicators = () => {
    if (runResults?.results) {
      return runResults.results.map(r => r.strategy).filter(Boolean);
    }
    return [];
  };
  const activeStrategies = getStrategyFromIndicators();
  const strategyDescriptions = {
    mean_reversion: {
      name: 'Mean Reversion Strategy',
      rules: 'Bollinger Bands (period=20, std=2.0) + RSI (period=14, threshold=30) regime filter',
      entry: 'Price ≤ Lower Band AND RSI < 30',
      exit: 'Price ≥ Middle Band OR RSI > 50',
    },
    trend_following: {
      name: 'Trend Following Strategy',
      rules: 'SMA Crossover (50/200) + MACD confirmation',
      entry: 'Close > SMA200 AND SMA50 > SMA200 AND MACD histogram > 0',
      exit: 'Close < SMA50 OR MACD histogram < 0',
    },
    trend_momentum_volume: {
      name: 'Trend + Momentum + Volume (TMV)',
      rules: 'Smoothed Heikin Ashi (30/5) + Range Filter (50, 2.5x) + Volume SMA(20)',
      entry: 'LONG: HA Bullish + Range Filter BUY + Volume > Avg | SHORT: HA Bearish + Range Filter SELL + Volume > Avg',
      exit: 'Trend reverses OR Range Filter flips OR 2:1 Stop/Target (1.5x/3.0x ATR)',
    },
    double_rsi: {
      name: 'Double RSI Strategy',
      rules: 'Trend RSI(21) + Signal RSI(7) - Dual timeframe approach',
      entry: 'Trend RSI > 60 (Bullish) AND Signal RSI crosses above 40',
      exit: 'Trend RSI < 40 OR Signal RSI crosses below 60 OR Stop/Target',
    },
  };

  if (!data.length) {
    return (
      <div className="chart-placeholder" style={{ height }}>
        No chart data. Select period and ensure backend is running.
      </div>
    );
  }

  if (chartError) {
    return (
      <div className="chart-placeholder" style={{ height, background: '#7f1d1d' }}>
        <div style={{ color: '#fca5a5', textAlign: 'center' }}>
          <div style={{ fontWeight: 'bold', marginBottom: '0.5rem' }}>⚠️ Chart Error</div>
          <div style={{ fontSize: '0.875rem' }}>{chartError}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="chart-section-wrapper">
      <div className="chart-wrapper" style={{ height, minHeight: '400px', backgroundColor: '#0f0f10' }}>
        <div ref={chartContainerRef} className="chart-container" style={{ width: '100%', height: '100%' }} />
      </div>

      {activeStrategies.length > 0 && (
        <div className="strategy-indicators-info">
          {activeStrategies.map(strategy => (
            <div key={strategy} className="indicator-description">
              <h4>{strategyDescriptions[strategy]?.name || strategy}</h4>
              <div className="indicator-details">
                <p><strong>Rules:</strong> {strategyDescriptions[strategy]?.rules}</p>
                <p><strong>Entry:</strong> {strategyDescriptions[strategy]?.entry}</p>
                <p><strong>Exit:</strong> {strategyDescriptions[strategy]?.exit}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
