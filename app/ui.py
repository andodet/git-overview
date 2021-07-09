import altair as alt
import pandas as pd
import streamlit as st
from pandas.tseries import offsets

import utils


def get_sidebar(data):
    st.sidebar.write(plot_cum_commits(data))

    contributors = data["author"].unique().tolist()
    contributors.insert(0, None)  # Manually add default

    # Filters
    contributor = st.sidebar.selectbox("Select Contributor", contributors, index=0)
    start = st.sidebar.date_input("Start Date", value=min(data["committed_on"]))
    end = st.sidebar.date_input("End Date", value=max(data["committed_on"]))

    # Data download button
    if st.sidebar.button("Download Data"):
        download_url = utils.download_data(data)
        st.sidebar.markdown(download_url, unsafe_allow_html=True)

    return start, end, contributor


def get_repo_source():
    input_type = st.sidebar.radio(
        "Input type input (.json/repo link)", ("Local .json", "Repo Link")
    )

    if input_type == "Local .json":
        repo_source = st.sidebar.file_uploader("Add your file here")
    elif input_type == "Repo Link":
        repo_source = st.sidebar.text_input("Add repo URL here", key="repo_url")

    return repo_source


def plot_top_contributors(data):
    bars = (
        alt.Chart(data[:30])
        .mark_bar()
        .encode(
            x=alt.X("n_commits", title="N. Commits"),
            y=alt.Y("author", sort="-x", title=""),
            tooltip=[
                alt.Tooltip("author", title="Author"),
                alt.Tooltip("n_commits", title="N. Commits", format=",.0f"),
            ],
        )
        .properties(width=850, height=430, title="Top 30 Contributors")
    )

    text = bars.mark_text(align="left", baseline="middle", dx=3).encode(
        text="n_commits:Q"
    )
    return bars + text


def plot_daily_contributions(data):
    agg = (
        data.groupby(pd.Grouper(key="committed_on", freq="1D"))["hash"]
        .count()
        .reset_index()
    )

    plot = (
        alt.Chart(agg)
        .mark_bar()
        .encode(
            x=alt.X("committed_on", title="Date"),
            y=alt.Y("hash", title="Commits", axis=alt.Axis(grid=False)),
            tooltip=[
                alt.Tooltip("committed_on", title="Date"),
                alt.Tooltip("hash", title="Commits"),
            ],
        )
        .properties(height=170, width=850, title="Daily Changes")
    )
    return plot


def plot_inserts_deletions(data):
    agg = data.copy()
    agg["lines_deleted"] = -agg["lines_deleted"]
    agg = (
        agg.groupby(pd.Grouper(key="committed_on", freq="1D"))[
            ["lines_added", "lines_deleted"]
        ]
        .sum()
        .reset_index()
        .melt(id_vars="committed_on")
    )

    plot = (
        alt.Chart(agg)
        .mark_bar()
        .encode(
            x=alt.X("committed_on", title="Date"),
            y=alt.Y("value", title=""),
            color=alt.condition(
                alt.datum.value > 0, alt.value("green"), alt.value("red")
            ),
            tooltip=[
                alt.Tooltip("committed_on", title="Date"),
                alt.Tooltip("value", title="Lines Changed", format=",.0f"),
                alt.Tooltip("variable"),
            ],
        )
    ).properties(height=170, width=850, title="Daily Lines Added/Removed")

    return plot


def plot_cum_commits(data):
    added_commits_cumsum = (
        data.groupby(pd.Grouper(key="committed_on", freq="1D"))["hash"]
        .count()
        .reset_index()
        .groupby(pd.Grouper(key="committed_on", freq="1M"))
        .sum()
        .cumsum()
        .reset_index()
    )

    plot = (
        alt.Chart(added_commits_cumsum)
        .mark_area()
        .encode(
            x=alt.X("committed_on:T", title="", axis=alt.Axis(labels=False)),
            y=alt.Y("hash:Q", title="", axis=alt.Axis(labels=False)),
            tooltip=[
                alt.Tooltip("committed_on", title="Date"),
                alt.Tooltip("hash", title="Commits", format=",.0f"),
            ],
        )
        .properties(width=300, height=100)
        .configure_axis(grid=False)
    )

    return plot


def plot_commit_waffle(data):
    daily_commits = (
        data.groupby(pd.Grouper(key="committed_on", freq="1D"))["hash"]
        .count()
        .reset_index()
    )
    daily_commits = daily_commits.set_index("committed_on")

    min_date = min(daily_commits.index) - offsets.YearBegin()
    max_date = max(daily_commits.index) + offsets.YearEnd()
    # Reindex by date
    idx = pd.date_range(min_date, max_date)
    daily_commits = daily_commits.reindex(idx, fill_value=0)
    daily_commits = daily_commits.rename_axis("committed_on").reset_index()
    # Add year and week to dataframe
    daily_commits["week"] = daily_commits["committed_on"].dt.isocalendar().week
    daily_commits["year"] = daily_commits["committed_on"].dt.year
    max_year = daily_commits["year"].max()

    # Year dropdown
    years = list(daily_commits["year"].unique())
    year_dropdown = alt.binding_select(options=years)
    selection = alt.selection_single(
        fields=["year"], bind=year_dropdown, name="Year", init={"year": max_year}
    )

    plot = (
        alt.Chart(daily_commits)
        .mark_rect()
        .encode(
            x=alt.X("week:O", title="Week"),
            y=alt.Y("day(committed_on):O", title=""),
            color=alt.Color(
                "hash:Q", scale=alt.Scale(range=["transparent", "green"]), title="Commits"
            ),
            tooltip=[
                alt.Tooltip("committed_on", title="Date"),
                alt.Tooltip("day(committed_on)", title="Day"),
                alt.Tooltip("hash", title="Commits"),
            ],
        )
        .add_selection(selection)
        .transform_filter(selection)
        .properties(width=1000, height=200)
    )

    return plot


def plot_cumulative_lines_by_contributor(data, n=20):
    top_n = (
        data.groupby("author")["hash"]
        .count()
        .sort_values(ascending=False)[:n]
        .index.tolist()
    )

    df_top_n_month = (
        data[data["author"].isin(top_n)]
        .groupby(["author", pd.Grouper(key="committed_on", freq="M")])["lines_added"]
        .sum()
        .reset_index()
    )

    min_month = df_top_n_month["committed_on"].min()
    max_month = df_top_n_month["committed_on"].max()

    idx = pd.MultiIndex.from_product(
        [pd.date_range(min_month, max_month, freq="M"), df_top_n_month["author"].unique()]
    )
    df_top_n_month = df_top_n_month.set_index(["committed_on", "author"])
    df_top_n_month = df_top_n_month["lines_added"].reindex(idx, fill_value=0).to_frame()
    df_top_n_month = df_top_n_month.rename_axis(["committed_on", "author"]).reset_index()
    # Cumulative df
    df_top_n_month = (
        df_top_n_month.groupby(["author", "committed_on"])["lines_added"]
        .sum()
        .groupby(level=0)
        .cumsum()
        .reset_index()
    )

    selection = alt.selection_single(on="mouseover")

    plot = (
        alt.Chart(df_top_n_month)
        .mark_area()
        .encode(
            x=alt.X("committed_on", title=""),
            y=alt.Y("lines_added", title="Lines Added"),
            color=alt.condition(selection, "author", alt.value("lightgray"), legend=None),
            tooltip=[
                alt.Tooltip("committed_on"),
                alt.Tooltip("lines_added", format=",.0f"),
                alt.Tooltip("author"),
            ],
        )
        .properties(
            width=800, height=350, title=f"Cumulative Lines Added by top-{n} Contributors"
        )
        .add_selection(selection)
    )

    return plot


def plot_quarterly_commits(data):
    plot = (
        alt.Chart(data)
        .mark_area()
        .encode(
            x=alt.X("committed_on", title=""),
            y=alt.Y("hash", title="Commits"),
            tooltip=[
                alt.Tooltip("committed_on", title="Date"),
                alt.Tooltip("hash", format=",.0f", title="Commits"),
            ],
        )
        .properties(width=500, height=130)
    )

    return plot
