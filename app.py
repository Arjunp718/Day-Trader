# app.py - Risk Sizer: a volatility-based position-sizing demo (educational, not advice)
import html

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="Risk Sizer", page_icon="📉", layout="wide")

TD = 252  # trading days per year
METHODS = ["Trailing 20-day volatility", "VIX only", "Average of trailing vol and VIX"]

# ---------------------------------------------------------------- look
SURFACE, INK, INK2, MUTED = "#F6F8FB", "#14202E", "#4B596A", "#7B8898"
GRID, BASE = "#E1E6ED", "#C8D0DB"
FONT = "Bricolage Grotesque, system-ui, -apple-system, Segoe UI, sans-serif"
C_RULE, C_BH, C_SAME = "#2a78d6", "#eb6834", "#1baf7a"   # chart series colors, in fixed order
NAMES = {"rule": "Rule (this app)", "bh": "Buy & hold", "same": "Buy & hold, same average exposure"}
COLORS = {NAMES["rule"]: C_RULE, NAMES["bh"]: C_BH, NAMES["same"]: C_SAME}
SHORT = {NAMES["rule"]: "Rule", NAMES["bh"]: "Buy & hold", NAMES["same"]: "Same-exposure buy & hold"}
COLORS_SHORT = {SHORT[k]: v for k, v in COLORS.items()}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,500;12..96,600&display=swap');
:root{--surface:#F6F8FB;--ink:#14202E;--ink2:#4B596A;--muted:#7B8898;--grid:#E1E6ED;--base:#C8D0DB;
--s1:#2a78d6;--cash:#DCE3EC;--warn:#fab219;}
html, body, .stApp, .stApp button, .stApp input, .stApp textarea,
[data-testid="stMarkdownContainer"], [data-testid="stSidebar"] label, [data-testid="stSidebar"] p
{font-family:'Bricolage Grotesque', system-ui, -apple-system, 'Segoe UI', sans-serif;}
.block-container{padding-top:2.2rem;padding-bottom:4rem;max-width:1160px;}
footer{visibility:hidden;}
.app-title{font-size:2.6rem;font-weight:600;letter-spacing:-0.025em;color:var(--ink);margin:0;line-height:1.1;}
.app-sub{color:var(--ink2);font-size:1.1rem;max-width:60ch;margin:.55rem 0 .3rem;line-height:1.45;}
.app-note{color:var(--muted);font-size:.92rem;margin:0 0 1.6rem;}
.sim-banner{border-left:4px solid var(--warn);background:#FFF6DF;padding:.7rem 1rem;color:var(--ink);
margin:0 0 1.4rem;border-radius:0 4px 4px 0;font-size:.98rem;}
.hero{display:grid;grid-template-columns:minmax(0,2.2fr) minmax(0,1fr);gap:2.5rem;padding:1.7rem 0 1.9rem;
border-top:1px solid var(--base);border-bottom:1px solid var(--base);margin-bottom:.6rem;}
.hero-cap{color:var(--ink2);font-size:1.02rem;}
.hero-fig{font-size:5.2rem;font-weight:600;line-height:1;letter-spacing:-0.03em;color:var(--ink);margin:.25rem 0 .15rem;}
.hero-sub{color:var(--ink2);font-size:1.15rem;margin-bottom:1.2rem;}
.split{display:flex;gap:2px;height:28px;}
.seg{border-radius:4px;display:flex;align-items:center;padding:0 10px;font-size:.85rem;font-weight:600;white-space:nowrap;}
.seg.stock{background:var(--s1);color:#fff;}
.seg.cash{background:var(--cash);color:var(--ink);}
.split-legend{display:flex;flex-wrap:wrap;gap:.4rem 1.5rem;margin-top:.75rem;color:var(--ink2);font-size:.97rem;}
.sw{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:.45rem;}
.hero-facts{margin:0;padding-left:2rem;border-left:1px solid var(--base);display:flex;flex-direction:column;
justify-content:center;gap:1.15rem;}
.hero-facts dt{color:var(--muted);font-size:.92rem;margin:0;}
.hero-facts dd{margin:0;color:var(--ink);font-size:1.4rem;font-weight:500;}
.sec-title{font-size:1.55rem;font-weight:600;letter-spacing:-0.012em;color:var(--ink);margin:2.4rem 0 .25rem;}
.sec-sub{color:var(--ink2);margin:0 0 1.1rem;max-width:72ch;line-height:1.45;}
[data-testid="stMarkdownContainer"] table.perf{width:100%;border-collapse:collapse;font-size:1rem;border:none;}
[data-testid="stMarkdownContainer"] table.perf th, [data-testid="stMarkdownContainer"] table.perf td{border:none;background:transparent;}
[data-testid="stMarkdownContainer"] table.perf th{text-align:right;font-weight:500;color:var(--muted);font-size:.92rem;padding:.55rem .8rem;border-bottom:1px solid var(--base);}
[data-testid="stMarkdownContainer"] table.perf td{text-align:right;padding:.85rem .8rem;border-bottom:1px solid var(--grid);color:var(--ink);font-variant-numeric:tabular-nums;}
[data-testid="stMarkdownContainer"] table.perf th:first-child, [data-testid="stMarkdownContainer"] table.perf td:first-child{text-align:left;padding-left:0;}
.tablewrap{overflow-x:auto;}
.key{display:inline-block;width:16px;height:3px;border-radius:2px;margin-right:.65rem;vertical-align:middle;}
.takeaway{margin:1.1rem 0 .4rem;color:var(--ink);font-size:1.06rem;max-width:72ch;line-height:1.5;}
.chart-title{font-weight:600;color:var(--ink);font-size:1.05rem;margin:1.6rem 0 0;}
.chart-sub{color:var(--muted);font-size:.9rem;margin:0;}
.legend{display:flex;flex-wrap:wrap;gap:.25rem 1.3rem;color:var(--ink2);font-size:.92rem;margin:.55rem 0 .1rem;}
.legend .key{margin-right:.45rem;}
.fine{color:var(--muted);font-size:.88rem;max-width:80ch;line-height:1.5;margin-top:2.5rem;}
@media (max-width: 760px){
[data-testid="stMarkdownContainer"] table.perf .hide-sm{display:none;}
[data-testid="stMarkdownContainer"] table.perf th, [data-testid="stMarkdownContainer"] table.perf td{padding-left:.4rem;padding-right:.4rem;font-size:.84rem;}
[data-testid="stMarkdownContainer"] table.perf th:first-child, [data-testid="stMarkdownContainer"] table.perf td:first-child{padding-left:0;min-width:7.2rem;}
.hero{grid-template-columns:1fr;gap:1.4rem;}
.hero-facts{border-left:none;padding-left:0;border-top:1px solid var(--base);padding-top:1.1rem;}
.hero-fig{font-size:4rem;}
.app-title{font-size:2.1rem;}}
</style>
"""


# ---------------------------------------------------------------- data
@st.cache_data(ttl=3600, show_spinner=False)
def load_close(ticker, start):
    """Daily closing prices (adjusted for splits and dividends)."""
    try:
        df = yf.download(ticker, start=start, auto_adjust=True, progress=False)
    except Exception:
        return pd.Series(dtype=float)
    if df is None or df.empty:
        return pd.Series(dtype=float)
    close = df["Close"].squeeze()
    if not isinstance(close, pd.Series):
        return pd.Series(dtype=float)
    return close.dropna()


@st.cache_data(show_spinner=False)
def simulated_close(start_year):
    """Made-up prices with calm and rough stretches (a GARCH-style simulation). Not real data."""
    rng = np.random.default_rng(11)
    idx = pd.bdate_range(f"{start_year}-01-01", pd.Timestamp.today().normalize())
    n = len(idx)
    r = np.zeros(n)
    v2 = 1.0e-4
    for i in range(n):
        if i:
            v2 = 2e-6 + 0.09 * r[i - 1] ** 2 + 0.89 * v2
        r[i] = rng.normal(0.0004, np.sqrt(v2))
    return pd.Series(100 * np.cumprod(1 + r), index=idx, name="Close")


# ---------------------------------------------------------------- logic
def forecast_log_vol(close, vix, method):
    """Forecast of log daily volatility, using only information known at each close."""
    ret = close.pct_change()
    lv20 = np.log(ret.rolling(20).std())
    if method == METHODS[0]:
        out = lv20
    else:
        lvix = np.log(vix.reindex(close.index).ffill() / 100 / np.sqrt(TD))  # VIX on a daily-vol scale
        out = lvix if method == METHODS[1] else (lv20 + lvix) / 2
    return out.replace([np.inf, -np.inf], np.nan)


def target_weight(log_daily_vol, target_vol, max_exposure, round_to):
    """Share of the account to hold: target volatility / forecast volatility, capped."""
    ann = np.exp(log_daily_vol) * np.sqrt(TD)
    w = np.clip(target_vol / ann, 0, max_exposure)
    if round_to:
        w = np.clip(np.round(w / round_to) * round_to, 0, max_exposure)
    return w


def summarize(r):
    eq = (1 + r).cumprod()
    years = len(r) / TD
    sd = r.std()
    return {
        "Total return": eq.iloc[-1] - 1,
        "Per year": eq.iloc[-1] ** (1 / years) - 1 if eq.iloc[-1] > 0 else np.nan,
        "Volatility": sd * np.sqrt(TD),
        "Worst drop": (eq / eq.cummax() - 1).min(),
        "Sharpe": r.mean() / sd * np.sqrt(TD) if sd > 0 else np.nan,
    }


def pct(x):
    return "n/a" if pd.isna(x) else f"{x:.1%}"


# ---------------------------------------------------------------- drawing helpers
def rgba(hex_color, alpha):
    h = hex_color.lstrip("#")
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{alpha})"


def line_chart(df, colors, yfmt, height=340, fill_first=False, yrange=None, step=False, legend=True):
    """Thin 2px lines, hairline grid, end dots with a surface ring, hover tooltip across all series."""
    fig = go.Figure()
    for i, col in enumerate(df.columns):
        s = df[col].dropna()
        fig.add_trace(go.Scatter(
            x=s.index, y=s.values, name=col, mode="lines",
            line=dict(color=colors[col], width=2, shape="hv" if step else "linear"),
            fill="tozeroy" if (fill_first and i == 0) else None,
            fillcolor=rgba(colors[col], 0.10) if (fill_first and i == 0) else None,
            hovertemplate=f"{col}: %{{y:{yfmt}}}<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=[s.index[-1]], y=[s.values[-1]], mode="markers", showlegend=False, hoverinfo="skip",
            marker=dict(size=9, color=colors[col], line=dict(width=2, color=SURFACE)),
        ))
    fig.update_layout(
        height=height,
        margin=dict(l=4, r=14, t=36 if legend else 8, b=8),
        paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
        font=dict(family=FONT, color=INK2, size=12),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#FFFFFF", bordercolor=BASE, font=dict(family=FONT, color=INK, size=12)),
        showlegend=legend,
        legend=dict(orientation="h", xanchor="left", x=0, yanchor="bottom", y=1.0,
                    font=dict(color=INK2, size=12), bgcolor="rgba(0,0,0,0)"),
    )
    fig.update_xaxes(showgrid=False, linecolor=BASE, tickfont=dict(color=MUTED), automargin=True,
                     showspikes=True, spikemode="across", spikecolor=MUTED, spikethickness=1, spikedash="solid")
    ytick = "~s" if (df.max().max() >= 10000 and "$" in yfmt) else yfmt
    fig.update_yaxes(showgrid=True, gridcolor=GRID, gridwidth=1, zeroline=False, showline=False,
                     tickfont=dict(color=MUTED), tickformat=ytick, automargin=True, range=yrange)
    return fig


def legend_html(colors):
    return '<div class="legend">' + "".join(
        f'<span><i class="key" style="background:{c}"></i>{html.escape(n)}</span>' for n, c in colors.items()) + "</div>"


def show(fig):
    st.plotly_chart(fig, theme=None, config={"displayModeBar": False})


def html_table(headers, rows, key_colors=None, hide_sm=()):
    """Plain HTML table (no blank lines or indentation, so Markdown leaves it alone).
    Columns named in hide_sm are dropped on phone-sized screens."""
    cls = [' class="hide-sm"' if h in hide_sm else "" for h in headers]
    head = "".join(f"<th{cls[i]}>{html.escape(h)}</th>" for i, h in enumerate(headers))
    body = ""
    for r in rows:
        first = html.escape(r[0])
        if key_colors and r[0] in key_colors:
            first = f'<span class="key" style="background:{key_colors[r[0]]}"></span>' + first
        body += "<tr><td>" + first + "</td>" + "".join(
            f"<td{cls[i + 1]}>{html.escape(str(c))}</td>" for i, c in enumerate(r[1:])) + "</tr>"
    return f'<div class="tablewrap"><table class="perf"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


# ---------------------------------------------------------------- sidebar
st.sidebar.header("Settings")
source = st.sidebar.radio("Prices", ["Live (Yahoo Finance)", "Simulated (demo)"],
                          help="Simulated prices are made up. Use them if live data is unavailable.")
sim = source.startswith("Simulated")
ticker_in = st.sidebar.text_input("Ticker (stock or ETF)", "SPY", disabled=sim).strip().upper()
method_in = st.sidebar.selectbox("Volatility forecast", METHODS, disabled=sim)
target_vol = st.sidebar.slider("Target volatility (% per year)", 5, 30, 15) / 100
max_exp = st.sidebar.slider("Max share of account in the stock (%)", 25, 100, 100) / 100
round_to = st.sidebar.selectbox("Round exposure to nearest", [0.05, 0.10, 0.25], index=1,
                                format_func=lambda x: f"{x:.0%}")
fee = st.sidebar.number_input("Trading cost per trade (%)", 0.0, 2.0, 0.10, 0.05) / 100
cash_rate = st.sidebar.number_input("Interest on cash (% per year)", 0.0, 10.0, 0.0, 0.5) / 100
start_year = st.sidebar.slider("History starts in", 2005, 2020, 2010)
account = st.sidebar.number_input("Pretend account size ($)", 100.0, 10_000_000.0, 1000.0, 100.0)

ticker = "SIM" if sim else ticker_in
method = METHODS[0] if sim else method_in
asset = "the simulated stock" if sim else html.escape(ticker)
asset_short = "Simulated stock" if sim else html.escape(ticker)

# ---------------------------------------------------------------- header
st.markdown(CSS, unsafe_allow_html=True)
st.markdown(
    '<h1 class="app-title">Risk Sizer</h1>'
    '<p class="app-sub">Decides how much of an account to hold by looking at how rough the market has been lately. '
    'It does not predict whether prices will rise or fall.</p>'
    '<p class="app-note">Educational project, not financial advice. It only simulates with past prices, '
    'and it does not connect to a broker or place trades.</p>',
    unsafe_allow_html=True,
)
if sim:
    st.markdown('<div class="sim-banner"><b>⚠ Simulated prices.</b> Everything below uses made-up data '
                'so the demo works offline. None of it is real market history.</div>', unsafe_allow_html=True)

if not ticker:
    st.stop()

start = f"{start_year}-01-01"
close = simulated_close(start_year) if sim else load_close(ticker, start)
if close.empty:
    st.error(f"No price data found for '{ticker}'. Check the symbol, or switch Prices to Simulated (demo).")
    st.stop()

vix = None
if method != METHODS[0]:
    vix = load_close("^VIX", start)
    if vix.empty:
        st.error("Could not load VIX data. Pick 'Trailing 20-day volatility' instead.")
        st.stop()

fc = forecast_log_vol(close, vix, method)
w = target_weight(fc, target_vol, max_exp, round_to)

valid = w.dropna()
if len(valid) < 120:
    st.warning("Not enough price history for this ticker and start year. Try an earlier start year.")
    st.stop()

# ---------------------------------------------------------------- today's readout
last_date = valid.index[-1]
w_now = float(valid.iloc[-1])
vol_now = float(np.exp(fc.loc[last_date]) * np.sqrt(TD))
stock_amt, cash_amt = account * w_now, account * (1 - w_now)

segs = ""
if w_now > 0.001:
    lab = f"{w_now:.0%}" if w_now >= 0.10 else ""
    segs += f'<div class="seg stock" style="flex:{w_now:.4f} 1 0">{lab}</div>'
if w_now < 0.999:
    lab = f"{1 - w_now:.0%}" if (1 - w_now) >= 0.10 else ""
    segs += f'<div class="seg cash" style="flex:{1 - w_now:.4f} 1 0">{lab}</div>'

st.markdown(
    '<div class="hero"><div>'
    f'<div class="hero-cap">What the rule says today for {asset}</div>'
    f'<div class="hero-fig">{w_now:.0%}</div>'
    f'<div class="hero-sub">of a &#36;{account:,.0f} account in {asset}, the rest in cash</div>'
    f'<div class="split" role="img" aria-label="{w_now:.0%} in {asset_short}, {1 - w_now:.0%} in cash">{segs}</div>'
    '<div class="split-legend">'
    f'<span><i class="sw" style="background:{C_RULE}"></i>{asset_short} &#36;{stock_amt:,.0f}</span>'
    f'<span><i class="sw" style="background:#DCE3EC"></i>Cash &#36;{cash_amt:,.0f}</span>'
    '</div></div>'
    '<dl class="hero-facts">'
    f'<div><dt>Expected volatility</dt><dd>{vol_now:.1%} a year</dd></div>'
    f'<div><dt>Target volatility</dt><dd>{target_vol:.0%} a year</dd></div>'
    f'<div><dt>Prices through</dt><dd>{last_date:%b %d, %Y}</dd></div>'
    '</dl></div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------- backtest
ret = close.pct_change()
held = w.shift(1)  # decide at today's close, earn tomorrow's return
bt = pd.DataFrame({"ret": ret, "held": held}).dropna()
if len(bt) < 60:
    st.warning("Not enough history to run the backtest.")
    st.stop()

turnover = bt["held"].diff().abs().fillna(bt["held"])
strat = bt["held"] * bt["ret"] + (1 - bt["held"]) * cash_rate / TD - turnover * fee
bh = bt["ret"]
avg_exp = bt["held"].mean()
same = avg_exp * bt["ret"] + (1 - avg_exp) * cash_rate / TD

results = {
    NAMES["rule"]: summarize(strat),
    NAMES["bh"]: summarize(bh),
    NAMES["same"]: summarize(same),
}
years = len(bt) / TD

st.markdown(
    '<div class="sec-title">How the rule would have done in the past</div>'
    f'<div class="sec-sub">{bt.index[0]:%b %d, %Y} to {bt.index[-1]:%b %d, %Y} ({years:.1f} years), '
    f'simulated with fake money. On average the rule held {avg_exp:.0%} of the account in the stock.</div>',
    unsafe_allow_html=True,
)

rows = [[name, pct(m["Total return"]), pct(m["Per year"]), pct(m["Volatility"]), pct(m["Worst drop"]),
         "n/a" if pd.isna(m["Sharpe"]) else f"{m['Sharpe']:.2f}"] for name, m in results.items()]
st.markdown(html_table(["", "Total return", "Per year", "Volatility", "Worst drop", "Sharpe"], rows, COLORS,
                       hide_sm=("Volatility",)), unsafe_allow_html=True)

# plain-language takeaway, computed from the numbers above
r_rule, r_bh, r_same = results[NAMES["rule"]], results[NAMES["bh"]], results[NAMES["same"]]
gap = (r_rule["Worst drop"] - r_same["Worst drop"]) * 100       # positive = rule's worst drop was smaller
yr = (r_rule["Per year"] - r_bh["Per year"]) * 100
if abs(gap) < 0.05:
    s1 = "The rule's worst drop was about the same as owning the same average amount all the time."
else:
    s1 = (f"The rule's worst drop was {abs(gap):.1f} points {'smaller' if gap > 0 else 'larger'} than owning "
          "the same average amount all the time, which is the fair comparison.")
if abs(yr) < 0.05:
    s2 = "Its yearly return was about the same as buy &amp; hold."
else:
    s2 = f"It earned {abs(yr):.1f} points {'more' if yr > 0 else 'less'} per year than buy &amp; hold."
st.markdown(f'<div class="takeaway">{s1} {s2}</div>', unsafe_allow_html=True)

curves = pd.DataFrame({
    NAMES["rule"]: (1 + strat).cumprod(),
    NAMES["bh"]: (1 + bh).cumprod(),
    NAMES["same"]: (1 + same).cumprod(),
}) * account
dd = curves / curves.cummax() - 1

left, right = st.columns(2)
with left:
    st.markdown(f'<div class="chart-title">What &#36;{account:,.0f} would have become</div>'
                '<div class="chart-sub">Hover to compare the three on any date</div>'
                + legend_html(COLORS_SHORT), unsafe_allow_html=True)
    show(line_chart(curves.rename(columns=SHORT), COLORS_SHORT, "$,.0f", legend=False))
with right:
    st.markdown('<div class="chart-title">Drops from the previous high</div>'
                '<div class="chart-sub">Closer to zero is a smoother ride</div>'
                + legend_html(COLORS_SHORT), unsafe_allow_html=True)
    show(line_chart(dd.rename(columns=SHORT), COLORS_SHORT, ".1%", fill_first=True,
                    yrange=[float(dd.min().min()) * 1.1, 0], legend=False))

st.markdown(f'<div class="chart-title">Share of the account held in {asset}</div>'
            '<div class="chart-sub">The rule holds less when the market gets rougher</div>', unsafe_allow_html=True)
show(line_chart(pd.DataFrame({"Share held": bt["held"]}), {"Share held": C_RULE}, ".0%", height=260,
                fill_first=True, yrange=[0, 1.02], step=True, legend=False))

# ---------------------------------------------------------------- details
with st.expander("Last 10 days of readouts"):
    recent = pd.DataFrame({"vol": (np.exp(fc) * np.sqrt(TD)).loc[valid.index].tail(10), "w": valid.tail(10)})
    st.markdown(html_table(["Date", "Expected volatility", "Share to hold"],
                           [[f"{d:%Y-%m-%d}", pct(r.vol), f"{r.w:.0%}"] for d, r in recent.iterrows()][::-1]),
                unsafe_allow_html=True)

with st.expander("How it works, and what it cannot do"):
    st.markdown(
        "- Each day it estimates how bumpy the market will be (volatility), then holds "
        "**target volatility / expected volatility** of the account, capped at your maximum. "
        "A rougher market means less stock and more cash.\n"
        "- In tests on SPY, QQQ, IWM, EFA, EEM and XLF (2013 to 2026), this kind of rule usually made the "
        "worst crash smaller, but it earned less than buy & hold and did not reliably improve "
        "return per unit of risk. On EEM, the smaller drop came only from holding less.\n"
        "- It cannot tell you whether a stock will rise or fall. Nothing here predicts prices.\n"
        "- The simulation trades at the closing price and ignores taxes. Past results do not predict "
        "future ones."
    )

st.markdown('<div class="fine">Educational project, not financial advice. Prices come from Yahoo Finance '
            'through the yfinance library and may be delayed or wrong. This app does not connect to a '
            'broker and does not place trades.</div>', unsafe_allow_html=True)
