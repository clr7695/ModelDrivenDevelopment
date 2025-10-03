# tests/test_repo_miner.py

import os
import pandas as pd
import pytest
from datetime import datetime, timedelta
from src.repo_miner import fetch_commits, fetch_issues#, merge_and_summarize
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
        DummyCommit("7fd1a60b01f91b314f59955a4e4d4e80d8edf11d", "The Octocat", "octocat@nowhere.com", datetime(2012,3,6,23,6,50), "Merge pull request #6 from Spaceghost/patch-1"),
        DummyCommit("762941318ee16e59dabbacb1b4049eec22f0d303", "Johnneylee Jack Rollins", "Johnneylee.rollins@gmail.com", datetime(2011,9,14,4,42,41), "New line at end of file. --Signed off by Spaceghost"),
        DummyCommit("553c2077f0edc3d5dc5d17262f6aa498e69d6f8e", "cameronmcefee", "cameron@github.com", datetime(2011,1,26,19,6,8), "first commit")
    ]
    gh_instance._repo = DummyRepo(commits, [])
    df = fetch_commits("any/repo", max_commits=1) # we know this repo has 3 commits, only get 1
    assert len(df) == 1

def test_fetch_commits_empty(monkeypatch):
    # TODO: Test that fetch_commits returns empty DataFrame when no commits exist.
    gh_instance._repo = DummyRepo([], []) # making a repo with no commits
    df = fetch_commits("any/repo")
    assert len(df) == 0


def test_fetch_issues_basic(monkeypatch):
    now = datetime.now()
    issues = [
        DummyIssue(1, 101, "Issue A", "alice", "open", now.strftime('%Y-%m-%d'), None, 0),
        DummyIssue(2, 102, "Issue B", "bob", "closed", (now - timedelta(days=2)).strftime('%Y-%m-%d'), now.strftime('%Y-%m-%d'), 2)
    ]
    gh_instance._repo = DummyRepo([], issues)
    df = fetch_issues("any/repo", state="all")
    assert {"id", "number", "title", "user", "state", "created_at", "closed_at", "comments"}.issubset(df.columns)
    assert len(df) == 2

def test_fetch_issues_no_pr(monkeypatch):
    now = datetime.now()
    issues = [
        DummyIssue(1, 101, "Issue A", "alice", "open", now.strftime('%Y-%m-%d'), None, 0),
        DummyIssue(2, 102, "Issue B", "bob", "closed", (now - timedelta(days=2)).strftime('%Y-%m-%d'), now.strftime('%Y-%m-%d'), 2, is_pr=True)
    ]
    gh_instance._repo = DummyRepo([], issues)
    df = fetch_issues("any/repo", state="all")
    assert {"id", "number", "title", "user", "state", "created_at", "closed_at", "comments"}.issubset(df.columns)
    assert len(df) == 1

def test_fetch_issues_date_parsing(monkeypatch):
    issues = [
        DummyIssue(1, 101, "Issue A", "alice", "open", '10/2/2025', None, 0),
        DummyIssue(2, 102, "Issue B", "bob", "closed", '2023-12-3', '10/2/2024', 2)
    ]
    gh_instance._repo = DummyRepo([], issues)
    df = fetch_issues("any/repo", state="all")
    assert {"id", "number", "title", "user", "state", "created_at", "closed_at", "comments"}.issubset(df.columns)
    print(df['created_at'])
    print(df["closed_at"])
    assert {"2025-10-02", "2023-12-03"}.issubset(df['created_at'])
    assert {'2024-10-02'}.issubset(df['closed_at'])

def test_fetch_issues_duration(monkeypatch):
    issues = [
        DummyIssue(1, 101, "Issue A", "alice", "open", '10/2/2025', None, 0),
        DummyIssue(2, 102, "Issue B", "bob", "closed", '2023-12-3', '10/2/2024', 2)
    ]
    gh_instance._repo = DummyRepo([], issues)
    df = fetch_issues("any/repo", state="all")
    assert {"id", "number", "title", "user", "state", "created_at", "closed_at", "comments"}.issubset(df.columns)
    print(df['open_duration_days'])
    assert df['open_duration_days'].isna().any()
    assert {304}.issubset(df['open_duration_days'])




