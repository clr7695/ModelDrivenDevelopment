#!/usr/bin/env python3
"""
repo_miner.py

A command-line tool to:
  1) Fetch and normalize commit data from GitHub

Sub-commands:
  - fetch-commits
"""

import os
import argparse
import pandas as pd
from github import Github, Auth

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
    # TODO

    # 2) Initialize client and get the repo
    # TODO

    # 3) Fetch issues, filtered by state ('all', 'open', 'closed')
    issues = repo.get_issues(state=state)

    # 4) Normalize each issue (skip PRs)
    records = []
    for idx, issue in enumerate(issues):
        if max_issues and idx >= max_issues:
            break
        # Skip pull requests
        # TODO

        # Append records
        # TODO

    # 5) Build DataFrame
    # TODO: return statement
    

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

if __name__ == "__main__":
    main()
