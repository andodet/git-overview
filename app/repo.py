import argparse
import csv
import json
from datetime import datetime

from pydriller import Repository
from tqdm import tqdm


def get_all_commits(path, since=None, to=None):
    """
    Grabs all commits and related metadata from a target repository.

    Args:
        path (str): A path to a local repository or a link to an hosted one
            (of the format https://github.com/andodet/myrepo.git).
        since (str): A date string of the format (`%Y-%m-%d`). Defaults to None.
        to (str):  A date string of the format (`%Y-%m-%d`). Defaults to None.
    Returns:
        list: A list of dictionaries of all commits and relative information.
    """
    if since and to:
        to = datetime.strptime(to, "%Y-%m-%d")
        since = datetime.strptime(since, "%Y-%m-%d")

    repo = Repository(path, num_workers=10, since=since, to=to)

    res = []
    print("Retrieving commits...")
    for commit in tqdm(repo.traverse_commits()):
        res.append(
            {
                "hash": commit.hash,
                "author": commit.author.name,
                "committed_on": commit.committer_date.strftime("%Y-%m-%d %H:%M:%S"),
                "authored_on": commit.author_date.strftime("%Y-%m-%d %H:%M:%S"),
                "lines_added": commit.insertions,
                "lines_deleted": commit.deletions,
                "files_touched": commit.files,
                # These two lines are accountable for a 10x slowdown runtime when
                #   processing commit histories. On a 7k commits repo this brings
                #   total runtime from 32min to ~3min.
                # "dmm_unit_complexity": commit.dmm_unit_complexity,
                # "dmm_unit_interfacing": commit.dmm_unit_interfacing,
                "is_merge": commit.merge,
                "message": commit.msg,
            }
        )
    print(f"✔️ {len(res)} commits downloaded for {path}")
    return res


def write_dataset(dataset, path, format):
    """
    Exports a commit history in .csv format

    Args:
        dataset (dict): A dataset returned by `get_all_commits` function.
        path (:obj:`str`, optional): Path for the output file
        format (:obj:`str`, optional): Format for the output file (suports 'json'and
            'csv')
    """
    format = format.lower()
    try:
        with open(path, "w") as f:
            if format == "csv":
                keys = dataset[0].keys()
                # with open(path, "w") as f:
                writer = csv.DictWriter(f, keys)
                writer.writeheader()
                writer.writerows(dataset)
            elif format == "json":
                # with open(path, "w") as f:
                json.dump(dataset, f)
    except (EnvironmentError) as e:
        raise e
    finally:
        print(f"{path} exported 🥳")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Extract commit hisotry and information from a target repo",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "repo_path",
        help="""The path of the repo. This can be a path on your machine or a link to
        a hosted service (e.g https://github.com/andodet/myrepo.git)""",
    )
    parser.add_argument("-f", "--output-format", help="Format of the output file")
    parser.add_argument("-o", "--output-path", help="Path of the output file")
    parser.add_argument("-s", "--since", help="Start date")
    parser.add_argument("-t", "--to", help="End date")
    parsed_args = parser.parse_args()

    commit_list = get_all_commits(
        parsed_args.repo_path, parsed_args.since, parsed_args.to
    )

    # Export .csv dataset if requested
    if parsed_args.output_path:
        write_dataset(commit_list, parsed_args.output_path, parsed_args.output_format)
