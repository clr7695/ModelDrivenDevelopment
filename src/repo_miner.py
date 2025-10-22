#!/usr/bin/env python3
"""
repo_miner.py

A command-line tool to:
  1) Fetch and normalize commit data from GitHub
  2) Fetch and normalize issue data from GitHub
  3) Merge data and print summary metrics

Sub-commands:
  - fetch-commits
  - fetch-issues
  - summarize
"""

import os
import argparse
import pandas as pd
from github import Github, Auth
from dateutil import parser

def fetch_commits(repo_name: str, max_commits: int = None) -> pd.DataFrame:
    """
    Fetch up to `max_commits` from the specified GitHub repository.
    Returns a DataFrame with columns: sha, author, email, date, message.
    """
    # 1) Read GitHub token from environment
    token = os.getenv("GITHUB_TOKEN")
    
    # 2) Initialize GitHub client and get the repo
    git = Github(token) # prove we have access with a token - this method is depreciated but the dummy code doesn't work if we do it the new way
    repo = git.get_repo(repo_name) # get the repo

    # 3) Fetch commit objects (paginated by PyGitHub)
    all_commits = []
    for commit in repo.get_commits(): #putting it from a paginated list to a regular list so its easier to work with
        all_commits.append(commit)

    # 4) Normalize each commit into a record dict
    commit_dicts = []
    cur_i = 0
    while (max_commits is None or cur_i < max_commits) and (cur_i < len(all_commits)): # check that we are under the max if it exists and don't cause an index error
        cur_commit = all_commits[cur_i]
        cur_dict = { # put the information in a dictionary format
            'sha': cur_commit.sha,
            'author': cur_commit.commit.author.name,
            'email': cur_commit.commit.author.email,
            'date': cur_commit.commit.author.date,
            'message': cur_commit.commit.message.split('\n')[0] # only get the first line
        }
        commit_dicts.append(cur_dict)
        cur_i += 1

    # 5) Build DataFrame from records
    df = pd.DataFrame(commit_dicts)
    return df

def fetch_issues(repo_name: str, state: str = "all", max_issues: int = None) -> pd.DataFrame:
    """
    Fetch up to `max_issues` from the specified GitHub repository (issues only).
    Returns a DataFrame with columns: id, number, title, user, state, created_at, closed_at, comments.
    """
    # 1) Read GitHub token
    token = os.getenv("GITHUB_TOKEN")

    # 2) Initialize client and get the repo
    git = Github(token) # prove we have access with a token - this method is depreciated but the dummy code doesn't work if we do it the new way
    repo = git.get_repo(repo_name) # get the repo

    # 3) Fetch issues, filtered by state ('all', 'open', 'closed')
    issues = repo.get_issues(state=state)

    # 4) Normalize each issue (skip PRs)
    records = []
    for idx, issue in enumerate(issues):
        if max_issues and idx >= max_issues:
            break
        # Skip pull requests
        if issue.pull_request:
            # print('Found Pull Request')
            continue
        # Append records
        rec = {
            'id': issue.id,
            'number': issue.number,
            'title': issue.title,
            'user': issue.user,
            'state': issue.state,
            'created_at': issue.created_at,
            'closed_at': issue.closed_at,
            'comments': issue.comments
        }
        records.append(rec)
    
    # 5) Build DataFrame
    df = pd.DataFrame(records)

    # sometimes we end up with only PRs, so it comes up as "zero" issues
    if len(df) == 0:
        print("No issues found. This might be because all issues fetched were pull requests.")
        return df

    # converting string dates to datetimes to subtract and then convert to a standardized string format
    df['created_at'] = pd.to_datetime(df['created_at'], format='mixed', utc=True)
    df['closed_at'] = pd.to_datetime(df['closed_at'], format='mixed', utc=True)
    open_duration_days = (df['closed_at'] - df['created_at']).dt.days
    df['created_at'] = df['created_at'].dt.strftime('%Y-%m-%d')
    df['closed_at'] = df['closed_at'].dt.strftime('%Y-%m-%d')

    df.insert(6, 'open_duration_days', open_duration_days)

    return df

def merge_and_summarize(commits_df: pd.DataFrame, issues_df: pd.DataFrame) -> None:
    """
    Takes two DataFrames (commits and issues) and prints:
      - Top 5 committers by commit count
      - Issue close rate (closed/total)
      - Average open duration for closed issues (in days)
    """
    # Copy to avoid modifying original data
    commits = commits_df.copy()
    issues  = issues_df.copy()

    # 1) Normalize date/time columns to pandas datetime
    commits['date'] = pd.to_datetime(commits['date'], errors='coerce')
    issues['created_at'] = pd.to_datetime(issues["created_at"], utc=True)
    issues['closed_at'] = pd.to_datetime(issues["closed_at"], utc=True)

    # 2) Top 5 committers
    top_committers = commits['author'].value_counts().head(5)
    top_c_names = top_committers.index.tolist()
    print("Top 5 committers:")
    for c in top_c_names:
        print(c + ": " + str(top_committers[c]) + " commits")
    print()

    # 3) Calculate issue close rate
    states = issues["state"].value_counts()
    closed = states["closed"] if "closed" in states.keys() else 0
    close_rate = round(closed/len(issues), 2)
    print("Issue close rate: " + str(close_rate))
    print()

    # 4) Compute average open duration (days) for closed issues
    issues["duration"] = issues["closed_at"] - issues["created_at"]
    issues["duration"] = issues["duration"].dt.days
    avg_duration = round(issues["open_duration_days"].mean(), 2)
    print("Avg. issue open duration: " + str(avg_duration) + " days")
    print()
    

def main():
    """
    Parse command-line arguments and dispatch to sub-commands.
    """
    parser = argparse.ArgumentParser(
        prog="repo_miner",
        description="Fetch GitHub commits/issues and summarize them"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Sub-command: fetch-commits
    c1 = subparsers.add_parser("fetch-commits", help="Fetch commits and save to CSV")
    c1.add_argument("--repo", required=True, help="Repository in owner/repo format")
    c1.add_argument("--max",  type=int, dest="max_commits",
                    help="Max number of commits to fetch")
    c1.add_argument("--out",  required=True, help="Path to output commits CSV")

    # Sub-command: fetch-issues
    c2 = subparsers.add_parser("fetch-issues", help="Fetch issues and save to CSV")
    c2.add_argument("--repo",  required=True, help="Repository in owner/repo format")
    c2.add_argument("--state", choices=["all","open","closed"], default="all",
                    help="Filter issues by state")
    c2.add_argument("--max",   type=int, dest="max_issues",
                    help="Max number of issues to fetch")
    c2.add_argument("--out",   required=True, help="Path to output issues CSV")

    # Sub-command: summarize
    c3 = subparsers.add_parser("summarize", help="Summarize commits and issues")
    c3.add_argument("--commits", required=True, help="Path to commits CSV file")
    c3.add_argument("--issues",  required=True, help="Path to issues CSV file")

    args = parser.parse_args()

    # Dispatch based on selected command
    if args.command == "fetch-commits":
        df = fetch_commits(args.repo, args.max_commits)
        df.to_csv(args.out, index=False)
        print(f"Saved {len(df)} commits to {args.out}")
    elif args.command == "fetch-issues":
        df = fetch_issues(args.repo, args.state, args.max_issues)
        df.to_csv(args.out, index=False)
        print(f"Saved {len(df)} issues to {args.out}")
    elif args.command == "summarize":
        # Read CSVs into DataFrames
        commits_df = pd.read_csv(args.commits)
        issues_df  = pd.read_csv(args.issues)
        # Generate and print the summary
        merge_and_summarize(commits_df, issues_df)

if __name__ == "__main__":
    main()
