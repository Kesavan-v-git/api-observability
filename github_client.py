import httpx
import base64

def fetch_file_from_github(owner: str, repo: str, file_path: str, token: str) -> str:
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }
    
    response = httpx.get(url, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"GitHub API error: {response.status_code} - {response.text}")
    
    data = response.json()
    encoded_content = data["content"]
    decoded_content = base64.b64decode(encoded_content).decode("utf-8")
    
    return decoded_content

def get_default_branch_sha(owner: str, repo: str, token: str) -> tuple[str, str]:
    """Returns (default_branch_name, latest_commit_sha)"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }
    
    # Get repo info to find the default branch name
    repo_url = f"https://api.github.com/repos/{owner}/{repo}"
    repo_resp = httpx.get(repo_url, headers=headers)
    if repo_resp.status_code != 200:
        raise Exception(f"Failed to get repo info: {repo_resp.text}")
    default_branch = repo_resp.json()["default_branch"]
    
    # Get the latest commit SHA on that branch
    ref_url = f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/{default_branch}"
    ref_resp = httpx.get(ref_url, headers=headers)
    if ref_resp.status_code != 200:
        raise Exception(f"Failed to get branch ref: {ref_resp.text}")
    sha = ref_resp.json()["object"]["sha"]
    
    return default_branch, sha


def create_branch(owner: str, repo: str, new_branch_name: str, from_sha: str, token: str):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }
    url = f"https://api.github.com/repos/{owner}/{repo}/git/refs"
    payload = {
        "ref": f"refs/heads/{new_branch_name}",
        "sha": from_sha
    }
    resp = httpx.post(url, headers=headers, json=payload)
    if resp.status_code not in (200, 201):
        raise Exception(f"Failed to create branch: {resp.text}")
    return resp.json()


def update_file_on_branch(owner: str, repo: str, file_path: str, new_content: str, 
                            branch: str, commit_message: str, token: str):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }
    
    # Need the current file's SHA to update it
    get_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}?ref={branch}"
    get_resp = httpx.get(get_url, headers=headers)
    if get_resp.status_code != 200:
        raise Exception(f"Failed to get file for update: {get_resp.text}")
    file_sha = get_resp.json()["sha"]
    
    # Update it
    put_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
    payload = {
        "message": commit_message,
        "content": base64.b64encode(new_content.encode("utf-8")).decode("utf-8"),
        "sha": file_sha,
        "branch": branch
    }
    put_resp = httpx.put(put_url, headers=headers, json=payload)
    if put_resp.status_code not in (200, 201):
        raise Exception(f"Failed to update file: {put_resp.text}")
    return put_resp.json()


def create_pull_request(owner: str, repo: str, branch: str, base: str, 
                         title: str, body: str, token: str):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    payload = {
        "title": title,
        "body": body,
        "head": branch,
        "base": base
    }
    resp = httpx.post(url, headers=headers, json=payload)
    if resp.status_code not in (200, 201):
        raise Exception(f"Failed to create PR: {resp.text}")
    return resp.json()