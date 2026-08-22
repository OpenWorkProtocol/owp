from __future__ import annotations

import json
import re
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from .errors import ValidationError

NAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


@dataclass(frozen=True)
class PRSnapshot:
    pr_url: str
    repo_owner: str
    repo_name: str
    pr_number: int
    title: str
    author_login: str
    state: str
    draft: bool
    head_sha: str
    head_ref: str
    base_ref: str
    additions: int
    deletions: int
    changed_files: int
    commits: int

    @property
    def size_band(self) -> str:
        churn = self.additions + self.deletions
        files = self.changed_files
        if churn <= 50 and files <= 3:
            return "small"
        if churn <= 250 and files <= 10:
            return "medium"
        if churn <= 1200 and files <= 30:
            return "large"
        return "very-large"


def parse_pr_url(url: str) -> tuple[str, str, int, str]:
    url = (url or "").strip()
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError as exc:
        raise ValidationError(
            "Use a public GitHub pull-request URL like https://github.com/owner/repo/pull/123"
        ) from exc
    if (
        parsed.scheme.lower() != "https"
        or (parsed.hostname or "").lower() != "github.com"
        or parsed.username
        or parsed.password
        or port is not None
    ):
        raise ValidationError(
            "Use a public GitHub pull-request URL like https://github.com/owner/repo/pull/123"
        )
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 4 or parts[2] != "pull" or not parts[3].isdigit() or int(parts[3]) < 1:
        raise ValidationError(
            "Use a public GitHub pull-request URL like https://github.com/owner/repo/pull/123"
        )
    owner, repo = parts[0], parts[1]
    if not NAME_RE.fullmatch(owner) or not NAME_RE.fullmatch(repo):
        raise ValidationError("The GitHub owner or repository name is invalid.")
    # GitHub owner/repository identity is case-insensitive. Normalizing prevents
    # the same PR from occupying several queue slots with casing variants.
    owner = owner.lower()
    repo = repo.lower()
    number = int(parts[3])
    canonical = f"https://github.com/{owner}/{repo}/pull/{number}"
    return owner, repo, number, canonical


class GitHubVerifier:
    """Verify that a submitted PR exists and snapshot useful size metadata."""

    def __init__(self, token: str | None = None, timeout: float = 8.0):
        self.token = token
        self.timeout = timeout

    def verify(self, pr_url: str) -> PRSnapshot:
        owner, repo, number, canonical = parse_pr_url(pr_url)
        api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "owp-field-lab/0.1",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = Request(api_url, headers=headers, method="GET")
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read(1_048_577)
                if len(raw) > 1_048_576:
                    raise ValidationError("GitHub returned an unexpectedly large response.")
                data = json.loads(raw.decode("utf-8"))
        except HTTPError as exc:
            if exc.code == 404:
                raise ValidationError("GitHub could not find that public pull request.") from exc
            if exc.code in {403, 429}:
                raise ValidationError(
                    "GitHub verification is rate-limited right now. Configure GITHUB_TOKEN or try again later."
                ) from exc
            raise ValidationError(f"GitHub verification failed with HTTP {exc.code}.") from exc
        except (URLError, TimeoutError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ValidationError("GitHub verification is temporarily unavailable.") from exc

        if data.get("state") != "open":
            raise ValidationError("The OWP field lab accepts open pull requests only.")

        head_sha = str((data.get("head") or {}).get("sha") or "")[:100]
        if not head_sha:
            raise ValidationError("GitHub did not provide a usable head commit for that PR.")

        def nonnegative_int(name: str) -> int:
            try:
                value = int(data.get(name) or 0)
            except (TypeError, ValueError) as exc:
                raise ValidationError(f"GitHub returned invalid PR metadata for {name}.") from exc
            if value < 0:
                raise ValidationError(f"GitHub returned invalid PR metadata for {name}.")
            return value

        return PRSnapshot(
            pr_url=canonical,
            repo_owner=owner,
            repo_name=repo,
            pr_number=number,
            title=str(data.get("title") or "(untitled PR)")[:500],
            author_login=str((data.get("user") or {}).get("login") or "unknown")[:100],
            state=str(data.get("state") or ""),
            draft=bool(data.get("draft")),
            head_sha=head_sha,
            head_ref=str((data.get("head") or {}).get("ref") or "")[:255],
            base_ref=str((data.get("base") or {}).get("ref") or "")[:255],
            additions=nonnegative_int("additions"),
            deletions=nonnegative_int("deletions"),
            changed_files=nonnegative_int("changed_files"),
            commits=nonnegative_int("commits"),
        )
