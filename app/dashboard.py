import streamlit as st

import ui
import utils


def body(commit_history):
    st.title("Git Repository Overview 👀")

    # Get filters
    start, end, contributor = ui.get_sidebar(commit_history)

    # Apply filters
    contributor_stats, q_contrib = utils.get_contributor_stats(
        commit_history, contributor
    )
    commit_history = utils.filter_by_date(commit_history, start, end)
    commit_history = utils.filter_by_contributor(commit_history, contributor)
    # Top-level repository stats
    st.markdown(
        """
    <style>
    .small-font {
        font-size:15px;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Top-level repo stats
    repo_stats = utils.get_repo_stats(commit_history)
    p1, p2 = st.beta_columns([1, 1])
    with st.beta_container():
        with p1:
            st.subheader("Repository Snapshot")
            for stat in repo_stats.items():
                st.markdown(
                    f"<p class='small-font'>{stat[1][1]} <strong>{stat[0]}</strong>: {stat[1][0]}</p>",  # noqa: E501
                    unsafe_allow_html=True,
                )

        with p2:
            try:
                st.subheader(f"Contributor: {contributor_stats.pop('Contributor')[0]}")
                for c_stat in contributor_stats.items():
                    st.markdown(
                        f"<p class='small-font'>{c_stat[1][1]} <strong>{c_stat[0]}</strong>: {c_stat[1][0]}</p>",  # noqa: E501
                        unsafe_allow_html=True,
                    )
                st.write(ui.plot_quarterly_commits(q_contrib))
            except (AttributeError, KeyError):
                pass

    st.markdown("---")
    st.write(ui.plot_commit_waffle(commit_history))
    with st.beta_expander("Changes Overview", expanded=True):
        st.write(ui.plot_daily_contributions(commit_history))
        st.write(ui.plot_inserts_deletions(commit_history))

    with st.beta_expander("Contributors Overview", expanded=True):
        st.write(ui.plot_top_contributors(utils.get_top_contributors(commit_history)))
        st.write(ui.plot_cumulative_lines_by_contributor(commit_history, 30))


if __name__ == "__main__":
    st.set_page_config(layout="wide")

    repo_source = ui.get_repo_source()
    try:
        commit_history = utils.get_data(repo_source)
        body = body(commit_history)
    except Exception as e:
        print(e)
        st.warning("Something went wrong when retrieving data!")
