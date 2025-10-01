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
    git = Github(auth=Auth.Token(token)) # prove we have access with a token
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
            'author': cur_commit.author.login,
            'email': cur_commit.author.email,
            'date': cur_commit.commit.author.date,
            'message': cur_commit.commit.message.split('\n')[0] # only get the first line
        }
        commit_dicts.append(cur_dict)
        cur_i += 1

    # 5) Build DataFrame from records
    df = pd.DataFrame(commit_dicts)
    return df
    

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

    args = parser.parse_args()

    # Dispatch based on selected command
    if args.command == "fetch-commits":
        df = fetch_commits(args.repo, args.max_commits)
        df.to_csv(args.out, index=False)
        print(f"Saved {len(df)} commits to {args.out}")

if __name__ == "__main__":
    main()
