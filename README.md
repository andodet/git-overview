# Git repository activity dashboard

This repo contains all the code produced for [this](https://anddt.com/post/streamlit-git-viz/) blog post. Through
the streamlit dashboard it's possible to explore the following metrics on a target git repository:

* Commits over time (waffle github-like activity chart)
* Top contributors
* Lines changed/added
* Cumulative lines changed by contributor
* Filter on specific time frame
* Drill down on a specific contributor

![](/static/dashboard.gif)

This dashboard is publicly available at [this url](https://share.streamlit.io/andodet/git-overview/app/dashboard.py).

## Usage

Run the streamlit app:
```sh
streamlit run app/dashboard.py
```

The dashboard can ingest data in two ways:
1. Provide a url for a remote repository (_disclaimer_: this solution might take a while to process long commit
histories). Consider using 2 if dealing with long commit histories.
2.  Upload a .json file exported using the `app/repo.py` utility.  
`app/repo.py` can be used in the following way:
```sh
$ python app/repo.py -h
usage: repo.py [-h] [-f OUTPUT_FORMAT] [-o OUTPUT_PATH] [-s SINCE] [-t TO] repo_path

Extract commit hisotry and information from a target repo

positional arguments:
  repo_path             The path of the repo. This can be a path on your machine or a link to
                                a hosted service (e.g https://github.com/andodet/myrepo.git)

optional arguments:
  -h, --help            show this help message and exit
  -f OUTPUT_FORMAT, --output-format OUTPUT_FORMAT
                        Format of the output file
  -o OUTPUT_PATH, --output-path OUTPUT_PATH
                        Path of the output file
  -s SINCE, --since SINCE
                        Start date
  -t TO, --to TO        End date
```

## Credits

This dashboard and blog post has been heavily inspired by [this](https://news.ycombinator.com/item?id=27689664)
hackernews post.

