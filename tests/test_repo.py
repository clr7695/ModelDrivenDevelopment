# tests/test_repo_miner.py

import os
import pandas as pd
import pytest
from datetime import datetime, timedelta
from src.repo_miner import fetch_commits#, fetch_issues, merge_and_summarize
from github import Github
from src import repo_miner

# --- Helpers for dummy GitHub API objects ---

class DummyAuthor:
    def __init__(self, name, email, date):
        self.name = name
        self.email = email
        self.date = date

class DummyCommitCommit:
    def __init__(self, author, message):
        self.author = author
        self.message = message

class DummyCommit:
    def __init__(self, sha, author, email, date, message):
        self.sha = sha
        self.commit = DummyCommitCommit(DummyAuthor(author, email, date), message)

class DummyUser:
    def __init__(self, login):
        self.login = login

class DummyIssue:
    def __init__(self, id_, number, title, user, state, created_at, closed_at, comments, is_pr=False):
        self.id = id_
        self.number = number
        self.title = title
        self.user = DummyUser(user)
        self.state = state
        self.created_at = created_at
        self.closed_at = closed_at
        self.comments = comments
        # attribute only on pull requests
        self.pull_request = DummyUser("pr") if is_pr else None

class DummyRepo:
    def __init__(self, commits, issues):
        self._commits = commits
        self._issues = issues

    def get_commits(self):
        return self._commits

    def get_issues(self, state="all"):
        # filter by state
        if state == "all":
            return self._issues
        return [i for i in self._issues if i.state == state]

class DummyGithub:
    def __init__(self, auth):
        assert auth == "fake-token"
    def get_repo(self, repo_name):
        # ignore repo_name; return repo set in test fixture
        return gh_instance._repo

@pytest.fixture(autouse=True)
def patch_env_and_github(monkeypatch):
    # Set fake token
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    # Patch Github class
    monkeypatch.setattr(repo_miner, "Github", DummyGithub)

# Helper global placeholder
gh_instance = DummyGithub("fake-token")

# --- Tests for fetch_commits ---
# An example test case
def test_fetch_commits_basic(monkeypatch):
    # Setup dummy commits
    now = datetime.now()
    commits = [
        DummyCommit("sha1", "Alice", "a@example.com", now, "Initial commit\nDetails"),
        DummyCommit("sha2", "Bob", "b@example.com", now - timedelta(days=1), "Bug fix")
    ]
    gh_instance._repo = DummyRepo(commits, [])
    df = fetch_commits("any/repo")
    assert list(df.columns) == ["sha", "author", "email", "date", "message"]
    assert len(df) == 2
    assert df.iloc[0]["message"] == "Initial commit"

def test_fetch_commits_limit(monkeypatch):
    # More commits than max_commits
    commits = [
        DummyCommit("7fd1a60b01f91b314f59955a4e4d4e80d8edf11d", "octocat", "octocat@github.com", datetime(2012,3,6,23,6,50), "Merge pull request #6 from Spaceghost/patch-1"),
        DummyCommit("762941318ee16e59dabbacb1b4049eec22f0d303", "Spaceghost", "git@spacegho.st", datetime(2011,9,14,4,42,41), "New line at end of file. --Signed off by Spaceghost"),
        DummyCommit("553c2077f0edc3d5dc5d17262f6aa498e69d6f8e", "Cameron423698", "", datetime(2011,1,26,19,6,8), "first commit")
    ]
    gh_instance._repo = DummyRepo(commits, [])
    df = fetch_commits("any/repo", max_commits=1) # we know this repo has 3 commits, only get 1
    assert len(df) == 1

def test_fetch_commits_empty(monkeypatch):
    # TODO: Test that fetch_commits returns empty DataFrame when no commits exist.
    gh_instance._repo = DummyRepo([], []) # making a repo with no commits
    df = fetch_commits("any/repo")
    assert len(df) == 0
