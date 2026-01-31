# 🔍 Chart Not Displaying - Complete Diagnostic & Fix

## Issues Identified & Fixed

### 1. **Indicator Extraction Error** ✅ FIXED
**Error**: `WARNING:backend.engine.backtester:Could not extract indicators: 'list' object has no attribute 'items'`

**Root Cause**: The backtesting.py library returns `_indicators` as a list in some cases, but the code was treating it as a dict.

**Fix Applied** (`backend/engine/backtester.py`):
```python
# Handle both dict and list formats
if isinstance(ind_data, dict):
    items = ind_data.items()
elif isinstance(ind_data, list):
    # If it's a list, create a dict with enumerated keys
    items = [(f"indicator_{i}", v) for i, v in enumerate(ind_data)]
```

---

### 2. **API Error Response Not Handled** ✅ FIXED
**Problem**: When `/api/data` returns a 400 error (no data), the frontend doesn't catch it

**Fix Applied** (`frontend/src/api/client.js`):
```javascript
if (!r.ok) {
  const errorText = await r.text();
  throw new Error(`Failed to fetch chart data: ${r.status} ${errorText}`);
}
```

---

### 3. **Time String Formatting Issues** ✅ FIXED
**Problem**: Time values with timezone info (e.g., `2025-01-31 00:00:00-05:00`) weren't parsing correctly

**Fix Applied** (`backend/app.py`):
```python
# Convert datetime to ISO string (just date part for consistency)
df_copy["time"] = pd.to_datetime(df_copy["time"]).dt.strftime("%Y-%m-%d")
```

---

### 4. **Missing Logging for Debugging** ✅ FIXED
**Problem**: Chart fails silently with no indication of what went wrong

**Fixes Applied**:

**Frontend** (`frontend/src/components/Chart.jsx`):
- Log when chart useEffect is called
- Log data length received
- Log OHLC parsing progress
- Log which records failed parsing and why
- Log when candlestick data is set

**Backend** (`frontend/src/api/client.js`):
- Log the API URL being called
- Log data points received
- Log any errors from the server

---

## Files Modified

### 1. `backend/engine/backtester.py`
**Lines**: 44-68
**Change**: Improved indicator extraction to handle both dict and list formats

### 2. `frontend/src/api/client.js`
**Lines**: 13-26
**Change**: Added proper error handling and logging to getData function

### 3. `backend/app.py`
**Lines**: 101-102
**Change**: Fixed time string formatting (date only, no timezone)
**Lines**: 106
**Change**: Only include required columns in response

### 4. `frontend/src/components/Chart.jsx`
**Lines**: 26-37
**Change**: Added console logging to chart initialization
**Lines**: 66-108
**Change**: Added detailed logging to OHLC parsing

---

## How to Diagnose Issues Now

### Step 1: Check Browser Console (F12)
Open your browser's developer console and look for logs from:

**When loading chart data:**
```
Fetching chart data from: /api/data?period_years=5&ticker=EURCHF%3DX&interval=1h&_t=...
Received 1000 data points
Chart useEffect triggered with: { dataLength: 1000, markersLength: 5, indicatorsKeys: ['SMA50', 'SMA200'] }
```

**If parsing OHLC:**
```
Parsed 1000 valid OHLC records from 1000 total records
Setting candlestick data with 1000 records
```

**If there's an issue:**
```
Unable to parse time from record 0: { time: "2025-01-31...", Open: 123.45, ... }
Invalid OHLC values at record 5: { open: NaN, high: 456, low: 123, close: 234 }
```

### Step 2: Check Backend Console
Look for logs like:
```
INFO:backend.data.yfinance_source:Downloading GC=F interval=1d period=5y
INFO:backend.data.cache:Saved cache: data_cache/GC_F_1d_5y.csv
INFO:werkzeug:127.0.0.1 - - [31/Jan/2026 03:10:43] "GET /api/data?..." 200 -
```

If you see `500` or `400` instead of `200`, there's a backend error.

---

## Testing Procedure

### Test 1: 1D Timeframe (Should work)
```
1. Refresh browser
2. Default settings: EUR/CHF, 1d
3. Open browser console
4. Click "Run backtest"
5. Verify logs show data points received
6. Verify chart displays
```

### Test 2: 1H Timeframe (Was broken, now fixed)
```
1. Change timeframe to "1 Hour"
2. Open browser console
3. Verify logs show:
   - "Received XXX data points"
   - "Parsed XXX valid OHLC records"
   - "Setting candlestick data with XXX records"
4. Verify chart displays (should show 2 years of hourly data)
```

### Test 3: 15M Timeframe (Was broken, now fixed)
```
1. Change timeframe to "15 Minutes"
2. Open browser console
3. Should see similar logs as 1H
4. Verify chart displays (should show 60 days of 15m data)
```

### Test 4: Different Symbol
```
1. Change symbol to "Gold (GC=F)"
2. Keep 1d timeframe
3. Click "Run backtest"
4. Should see cache save: "data_cache/GC_F_1d_5y.csv"
5. Chart should display
```

---

## Common Issues & Solutions

### Issue: Browser shows "Failed to load chart data: 500"
**Cause**: Backend error
**Solution**: Check backend console for error details

### Issue: Browser shows "No OHLC data available"
**Cause**: All data points failed to parse
**Solution**: Check browser console logs for "Unable to parse time" or "Invalid OHLC values"

### Issue: Chart renders but no candlesticks show
**Cause**: OHLC data exists but values are incorrect
**Solution**: Check browser console - should see "Setting candlestick data" message

### Issue: "Could not extract indicators" warning but chart works
**Cause**: Indicators failed to extract, but chart still renders
**Solution**: This is now fixed. If still seeing this, indicators will show as empty in chart

---

## How the Fix Works

### Data Flow (After Fixes)

```
User selects timeframe (e.g., 1h)
                  ↓
Browser console logs: "Fetching chart data from: /api/data?..."
                  ↓
Backend retrieves/downloads data, converts to JSON
                  ↓
Backend logs: "Cached 1000 records for EUR/CHF 1h 5y"
                  ↓
Frontend receives response, logs: "Received 1000 data points"
                  ↓
Frontend parses OHLC values
  └─ Logs: "Parsed 1000 valid OHLC records from 1000 total records"
                  ↓
Frontend creates chart
  └─ Logs: "Setting candlestick data with 1000 records"
                  ↓
Chart renders on screen ✅
```

---

## Performance Notes

- **First run**: Might be slow (downloading data)
- **Subsequent runs**: Fast (cached data)
- **Logging overhead**: Minimal - only console.log statements
- **Can disable logging**: Remove or comment out console.log lines in production

---

## Next Steps

1. **Restart servers** with these fixes
2. **Test each timeframe** (1d, 1h, 15m, 4h, 1m)
3. **Monitor browser console** for logs
4. **Try different symbols**
5. **Report any issues** with console logs and backend logs

---

**Status**: ✅ All diagnostic logging added
**Ready for**: Testing with detailed feedback
