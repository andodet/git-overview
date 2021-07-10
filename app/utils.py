import base64

import pandas as pd
import streamlit as st
from streamlit.uploaded_file_manager import UploadedFile

from repo import get_all_commits


@st.cache
def get_data(repo_path):
    """
    Retrieve commit history from remote source or local .json file

    Args:
        repo_path: File st.text_input or st.file_uploader
    Returns:
        pandas.DataFrame: A dataframae containing the commit history
    """
    if isinstance(repo_path, UploadedFile):
        data = pd.read_json(repo_path, orient="records")
    else:
        commits = get_all_commits(repo_path)
        data = pd.DataFrame(commits)

    # Convert timestamps
    data[["committed_on", "authored_on"]] = data[["committed_on", "authored_on"]].apply(
        pd.to_datetime
    )
    data['total_lines'] = data['lines_added'] + data['lines_deleted']

    return data


def get_top_contributors(data):
    """Rank contributors by number of commits"""
    # fmt: off
    res = (
        data.groupby("author")["hash"]
            .count()
            .sort_values(ascending=False)
            .reset_index()
    )
    res.columns = ["author", "n_commits"]
    return res


def get_repo_stats(data):
    """Get some high level repository statistics"""
    repo_stats = {
        "Commits": (f"{data['hash'].count():,}", "📃"),
        "Merges": (f"{data['is_merge'].value_counts()[0]:,}", "⛙"),
        "Contributors": (f"{data['author'].nunique():,}", "👨‍💻"),
        "Lines Added": (f"{data['lines_added'].sum():,}", "➕"),
        "Lines Deleted": (f"{data['lines_deleted'].sum():,}", "➖")
    }

    return repo_stats


def get_contributor_stats(data, contributor):
    """
    Gets some high level statistics on a given contributor

    Args:
        data (pd.DataFrame): A commit history
        contributor (str): The name of the target contributor
    Returns:
        (tuple): tuple containing:

            stats (dict): Dict containing contributor metrics
            quarterly_contrib (pd.DataFrame): Dataframe with n. contributions by quarter.
    """
    if not contributor:
        return None, None

    activity = data[data['author'] == contributor]
    n_commits = len(activity)

    # Lines of code stats
    tot_lines = activity['lines_added'].sum() + activity['lines_deleted'].sum()
    pct_change = n_commits / len(data)
    tot_l_added = activity['lines_added'].sum()
    tot_l_deleted = activity['lines_deleted'].sum()
    pct_l_deleted = tot_l_deleted / tot_lines
    pct_l_added = tot_l_added / tot_lines
    avg_change = activity['total_lines'].mean()

    # Total changes by quarter
    quarterly_contrib = (
        activity.groupby(pd.Grouper(key='committed_on', freq="1Q"))['hash']
            .count()  # noqa: E131
            .reset_index()
    )
    return {
        "Commits": (f"{n_commits}", "📜"),
        "Total Lines": (f"{tot_lines:,}", "🖋️"),
        "Lines Added": (f"{tot_l_added:,}", "🖋️"),
        "% Lines Added": (f"{pct_l_added * 100:,.3}", "✅"),
        "Lines Deleted": (f"{tot_l_deleted:,}", "❌"),
        "% Lines Deleted": (f"{pct_l_deleted * 100:,.3}", "❌"),
        "% of Total Changes": (f"{pct_change * 100:,.3}", "♻️"),
        "Avg. Change (lines)": (f"{avg_change:,.2f}", "♻️"),
        "Contributor": (contributor, "👨‍💻")
    }, quarterly_contrib


def filter_by_date(df, start, end):
    """Filter dataframe by date"""
    df = df[(df['committed_on'] >= str(start)) & (df['committed_on'] <= str(end))]
    return df


def filter_by_contributor(df, x):
    """Filter dataframe by contributor"""
    if not x:
        return df
    else:
        df = df[df['author'] == x]
        return df


def download_data(data):
    """
    Download data in .csv format
    Args:
        data (`pd.DataFrame`): A pandas dataframe
    Returns:
        str: A href link to be fed into the dashboard ui.
    """
    to_download = data.to_csv(index=False)
    b64 = base64.b64encode(to_download.encode()).decode()
    href = f'<a href="data:file/text;base64,{b64}">Download csv file</a>'

    return href
