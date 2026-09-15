import time
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Watchlist Explorer", layout="wide")
st.title("Watchlist Explorer")
st.caption("Six tech stocks, weekly, 2018-2019. Indexed to 1.00 on 2018-01-01.")

@st.cache_data
def load_data():
    time.sleep(2) # stand-in for a slow API / database call — delete in a real app
    wide = px.data.stocks()
    wide["date"] = pd.to_datetime(wide["date"])
    long = wide.melt(id_vars="date", var_name="ticker", value_name="price")
    return long.sort_values(["ticker", "date"])

df = load_data()
with st.sidebar:
    st.header("Controls")
    tickers = st.multiselect(
        "Tickers",
        options=sorted(df["ticker"].unique()),
        default=["AAPL", "MSFT", "AMZN"],
    )
    start, end = st.slider(
        "Date range",
        min_value=df["date"].min().date(),
        max_value=df["date"].max().date(),
        value=(df["date"].min().date(), df["date"].max().date()),
    )
    rebase = st.checkbox("Rebase to 100 at window start", value=True)

view = df[df["ticker"].isin(tickers) & df["date"].dt.date.between(start, end)].copy()

if view.empty:
    st.info("Pick at least one ticker in the sidebar.")
    st.stop()

if rebase:
    view["price"] = view.groupby("ticker")["price"].transform(lambda s: s / s.iloc[0] *
    100)

perf = view.groupby("ticker")["price"].agg(["first", "last"])
perf["return_%"] = (perf["last"] / perf["first"] - 1) * 100
best = perf["return_%"].idxmax()

c1, c2, c3 = st.columns(3)
c1.metric("Tickers", len(tickers))
c2.metric("Weeks in window", view["date"].nunique())
c3.metric(f"Best: {best}", f"{perf.loc[best, 'return_%']:+.1f}%")

fig = px.line(
    view,
    x="date",
    y="price",
    color="ticker",
    labels={"price": "Rebased (start = 100)" if rebase else "Index (2018-01-01 = 1.00)",
        "date": ""},
)
fig.update_layout(height=420, margin=dict(t=10, b=0), legend_title_text="")
st.plotly_chart(fig)

if "pinned" not in st.session_state:
    st.session_state.pinned = []

left, right, _ = st.columns([1, 1, 4])
if left.button("Pin this view"):
    st.session_state.pinned.append(
        {
            "tickers": ", ".join(tickers),
            "from": start,
            "to": end,
            "best": best,
            "return_%": round(float(perf.loc[best, "return_%"]), 1),
        }
    )
if right.button("Clear pins"):
    st.session_state.pinned = []
if st.session_state.pinned:
    st.subheader("Pinned views")
    st.dataframe(pd.DataFrame(st.session_state.pinned), hide_index=True)

st.download_button(
    "Download filtered data (CSV)",
    data=view.to_csv(index=False).encode("utf-8"),
    file_name="watchlist.csv",
    mime="text/csv",
)