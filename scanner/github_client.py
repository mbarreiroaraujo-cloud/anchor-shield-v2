"""GitHub API integration for scanning remote repositories."""

import os
import re
import json
import time
import base64
from urllib.parse import urlparse
from typing import Optional

import requests


class GitHubClient:
    """Client for fetching repository files and searching for vulnerable patterns."""

    API_BASE = "https://api.github.com"

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.environ.get("GITHUB_TOKEN", "")
        self.session = requests.Session()
        if self.token:
            self.session.headers["Authorization"] = f"token {self.token}"
        self.session.headers["Accept"] = "application/vnd.github.v3+json"
        self.session.headers["User-Agent"] = "anchor-shield/0.1.0"
        self._rate_limit_remaining = 60
        self._rate_limit_reset = 0

    def parse_repo_url(self, url: str) -> tuple[str, str]:
        """Parse GitHub URL to owner/repo."""
        url = url.rstrip("/")
        if url.startswith("https://github.com/"):
            parts = url.replace("https://github.com/", "").split("/")
            if len(parts) >= 2:
                return parts[0], parts[1].replace(".git", "")
        # Try owner/repo format directly
        parts = url.split("/")
        if len(parts) == 2:
            return parts[0], parts[1]
        raise ValueError(f"Cannot parse GitHub URL: {url}")

    def fetch_repo_files(
        self,
        repo_url: str,
        extensions: list[str] | None = None,
        max_files: int = 100,
    ) -> dict[str, str]:
        """Fetch source files from a GitHub repository.

        Returns dict of {filepath: content}.
        """
        if extensions is None:
            extensions = [".rs"]

        owner, repo = self.parse_repo_url(repo_url)

        # Get the default branch
        repo_info = self._api_get(f"/repos/{owner}/{repo}")
        if not repo_info:
            raise ConnectionError(f"Could not access repository: {owner}/{repo}")
        default_branch = repo_info.get("default_branch", "main")

        # Get the file tree
        tree = self._api_get(
            f"/repos/{owner}/{repo}/git/trees/{default_branch}",
            params={"recursive": "1"},
        )
        if not tree or "tree" not in tree:
            raise ConnectionError(f"Could not fetch file tree for {owner}/{repo}")

        # Filter to desired extensions
        target_files = []
        for item in tree["tree"]:
            if item["type"] != "blob":
                continue
            # Skip build artifacts
            path = item["path"]
            if any(skip in path for skip in ["target/", "node_modules/", ".git/"]):
                continue
            if any(path.endswith(ext) for ext in extensions):
                target_files.append(path)

        # Limit files
        target_files = target_files[:max_files]

        # Fetch content for each file
        files = {}
        for filepath in target_files:
            content = self._fetch_file_content(owner, repo, filepath, default_branch)
            if content is not None:
                files[filepath] = content
            self._respect_rate_limit()

        return files

    def count_pattern_usage(self, query: str) -> int:
        """Count how many code results match a pattern on GitHub."""
        try:
            result = self._api_get(
                "/search/code",
                params={"q": f"{query} language:rust"},
            )
            if result:
                return result.get("total_count", 0)
        except Exception:
            pass
        return 0

    def find_affected_repos(self, query: str, min_stars: int = 10) -> list[dict]:
        """Find well-known repos using a specific pattern."""
        try:
            result = self._api_get(
                "/search/repositories",
                params={
                    "q": f"{query} language:rust stars:>{min_stars}",
                    "sort": "stars",
                    "per_page": "10",
                },
            )
            if result and "items" in result:
                return [
                    {
                        "name": r["full_name"],
                        "url": r["html_url"],
                        "stars": r["stargazers_count"],
                        "description": r.get("description", ""),
                    }
                    for r in result["items"]
                ]
        except Exception:
            pass
        return []

    def _fetch_file_content(
        self, owner: str, repo: str, path: str, branch: str
    ) -> Optional[str]:
        """Fetch raw file content from GitHub."""
        try:
            result = self._api_get(
                f"/repos/{owner}/{repo}/contents/{path}",
                params={"ref": branch},
            )
            if result and "content" in result:
                return base64.b64decode(result["content"]).decode("utf-8", errors="ignore")
        except Exception:
            pass
        return None

    def _api_get(self, endpoint: str, params: dict | None = None) -> Optional[dict]:
        """Make a GET request to the GitHub API with rate limit handling."""
        url = f"{self.API_BASE}{endpoint}"
        try:
            resp = self.session.get(url, params=params, timeout=15)

            # Track rate limits
            self._rate_limit_remaining = int(
                resp.headers.get("X-RateLimit-Remaining", 60)
            )
            self._rate_limit_reset = int(
                resp.headers.get("X-RateLimit-Reset", 0)
            )

            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 403 and self._rate_limit_remaining == 0:
                # Rate limited
                wait = max(0, self._rate_limit_reset - int(time.time())) + 1
                if wait <= 60:
                    time.sleep(wait)
                    return self._api_get(endpoint, params)
        except requests.exceptions.RequestException:
            pass
        return None

    def _respect_rate_limit(self):
        """Sleep if approaching rate limit."""
        if self._rate_limit_remaining < 5:
            wait = max(0, self._rate_limit_reset - int(time.time())) + 1
            if wait <= 60:
                time.sleep(wait)
