import os
import json
from dotenv import load_dotenv
import requests
import subprocess
from tqdm import tqdm
import time

# Load environment variables from .env file
load_dotenv()

# Load Bitbucket credentials from environment variables
bitbucket_user = os.getenv('BITBUCKET_USER')
bitbucket_pass = os.getenv('BITBUCKET_PASS')
bitbucket_org = os.getenv('BITBUCKET_ORG')

# Load GitHub credentials from environment variables
github_user = os.getenv('GITHUB_USER')
github_access_token = os.getenv('GITHUB_ACCESS_TOKEN')
github_org = os.getenv('GITHUB_ORG')

# Load author and committer names and emails from environment variables
git_author_name_old1 = os.getenv('GIT_AUTHOR_NAME_OLD1')
git_author_name_old2 = os.getenv('GIT_AUTHOR_NAME_OLD2')
git_author_name_old3 = os.getenv('GIT_AUTHOR_NAME_OLD3')
git_author_name_new = os.getenv('GIT_AUTHOR_NAME_NEW')
git_author_email_new = os.getenv('GIT_AUTHOR_EMAIL_NEW')
git_committer_name_new = os.getenv('GIT_COMMITTER_NAME_NEW')
git_committer_email_new = os.getenv('GIT_COMMITTER_EMAIL_NEW')

def get_bitbucket_repos_page(url):
    r = requests.get(url, auth=(bitbucket_user, bitbucket_pass))
    if r.status_code == 200:
        return r.json()
    else:
        print(f"Error: {r.status_code}")
        return None

def get_bitbucket_repos():
    repos = []
    api_url = f"https://api.bitbucket.org/2.0/repositories/{bitbucket_org}"
    response = get_bitbucket_repos_page(api_url)
    if response:
        values = response["values"]
        while "next" in response:
            print(f"getting {response['next']}")
            response = get_bitbucket_repos_page(response["next"])
            if response:
                values = values + response["values"]
            else:
                break

        for repo in values:
            for clonelink in repo["links"]["clone"]:
                if clonelink["name"] == "https":
                    repos.append((repo["name"], clonelink["href"]))
    return repos

def create_github_name(bitbucket_name):
    parts = bitbucket_name.split("_")
    if parts[0].isdigit():
        job_no = parts.pop(0)
        parts.append(job_no)
    return "bb_" + "_".join(parts).lower().replace(" ", "")

def get_github_origin(repo_name):
    return f"https://github.com/{github_user}/{repo_name}.git"

def is_github_repo_empty(repo_name):
    api_url = f"https://api.github.com/repos/{github_user}/{repo_name}"
    headers = {
        "Authorization": f"token {github_access_token}",
        "Accept": "application/vnd.github.v3+json",
    }
    r = requests.get(api_url, headers=headers)
    if r.status_code == 200:
        repo_info = r.json()
        return repo_info['size'] == 0
    elif r.status_code == 404:
        return True  # Repository does not exist
    else:
        print(f"Error checking GitHub repo: {r.status_code}")
        print(f"Response: {r.text}")
        return False

def create_github_repo(repo_name, last_create_time):
    min_interval = 2  # Minimum interval between create operations in seconds
    elapsed_time = time.time() - last_create_time
    if elapsed_time < min_interval:
        time.sleep(min_interval - elapsed_time)
    
    api_url = f"https://api.github.com/user/repos"  # For personal accounts
    headers = {
        "Authorization": f"token {github_access_token}",
        "Accept": "application/vnd.github.v3+json",
    }
    data = json.dumps({
        "name": repo_name,
        "private": True,
    })
    r = requests.post(api_url, headers=headers, data=data)
    if r.status_code == 201:
        return True, time.time()
    else:
        print(f"Error creating GitHub repo: {r.status_code}")
        print(f"Response: {r.text}")
        return False, time.time()

def archive_github_repo(repo_name):
    api_url = f"https://api.github.com/repos/{github_user}/{repo_name}"
    r = requests.patch(
        api_url,
        data=json.dumps({"archived": True}),
        headers={
            "Authorization": f"token {github_access_token}",
            "Accept": "application/vnd.github.v3+json",
        },
    )
    if r.status_code == 200:
        print(f"Archived {repo_name}")
    else:
        print(f"Error archiving GitHub repo: {r.status_code}")

def unarchive_github_repo(repo_name):
    api_url = f"https://api.github.com/repos/{github_user}/{repo_name}"
    r = requests.patch(
        api_url,
        data=json.dumps({"archived": False}),
        headers={
            "Authorization": f"token {github_access_token}",
            "Accept": "application/vnd.github.v3+json",
        },
    )
    if r.status_code == 200:
        print(f"Unarchived {repo_name}")
    else:
        print(f"Error unarchiving GitHub repo: {r.status_code}")

def clone(bitbucket_origin, path):
    process = subprocess.Popen(
        ["git", "clone", "--mirror", bitbucket_origin, path], stdout=subprocess.PIPE
    )
    process.communicate()[0]

def remove_large_files(path, size_limit=100):
    # Convert size limit to bytes
    size_limit_bytes = size_limit * 1024 * 1024

    # Run git filter-repo to remove large files
    process = subprocess.Popen(
        [
            "git",
            "filter-repo",
            "--strip-blobs-bigger-than",
            f"{size_limit_bytes}B"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=path,
    )
    stdout, stderr = process.communicate()
    print(stdout.decode())
    print(stderr.decode())

def rewrite_git_history(path):
    process = subprocess.Popen(
        [
            "git",
            "filter-branch",
            "--env-filter",
            f"""
            AUTHOR_NAME_LOWER=$(echo "$GIT_AUTHOR_NAME" | tr '[:upper:]' '[:lower:]')
            COMMITTER_NAME_LOWER=$(echo "$GIT_COMMITTER_NAME" | tr '[:upper:]' '[:lower:]')
            if [ "$AUTHOR_NAME_LOWER" = "{git_author_name_old1}" ] || [ "$AUTHOR_NAME_LOWER" = "{git_author_name_old2}" ] || [ "$AUTHOR_NAME_LOWER" = "{git_author_name_old3}" ]; then
                GIT_AUTHOR_NAME='{git_author_name_new}'
                GIT_AUTHOR_EMAIL='{git_author_email_new}'
            fi
            if [ "$COMMITTER_NAME_LOWER" = "{git_author_name_old1}" ] || [ "$COMMITTER_NAME_LOWER" = "{git_author_name_old2}" ] || [ "$COMMITTER_NAME_LOWER" = "{git_author_name_old3}" ]; then
                GIT_COMMITTER_NAME='{git_committer_name_new}'
                GIT_COMMITTER_EMAIL='{git_committer_email_new}'
            fi
            """,
            "--tag-name-filter",
            "cat",
            "--",
            "--branches",
            "--tags",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=path,
    )
    stdout, stderr = process.communicate()
    print(stdout.decode())
    print(stderr.decode())

def lfs(path):
    conf = []

def push(github_origin, path):
    process = subprocess.Popen(
        ["git", "push", "--mirror", github_origin], stdout=subprocess.PIPE, cwd=path
    )
    process.communicate()[0]

def delete(path):
    process = subprocess.Popen(["rm", "-rf", path], stdout=subprocess.PIPE)
    process.communicate()[0]

def migrate(bb_repo_name, bb_repo_clone_url, last_create_time):
    repo_clone_url = "".join(
        [
            bb_repo_clone_url.split("@")[0],
            ":",
            bitbucket_pass,
            "@",
            bb_repo_clone_url.split("@")[1],
        ]
    )
    print(f"bb_repo_name: {bb_repo_name}")
    print(f"bb_repo_clone_url: {bb_repo_clone_url}")
    gh_repo = create_github_name(bb_repo_name)
    print(f"{bb_repo_name} converted to {gh_repo}")

    if not is_github_repo_empty(gh_repo):
        print(f"GitHub repo {gh_repo} already exists and is not empty, skipping creation.")
    else:
        success, last_create_time = create_github_repo(gh_repo, last_create_time)
        if not success:
            print("failed to create GH repo ")
            return last_create_time
        print("new GH repo created")

    local_path = os.path.abspath(os.path.join("tmp_data", gh_repo))
    delete(local_path)
    clone(repo_clone_url, local_path)
    print(f"cloned to {local_path}")
    remove_large_files(local_path)  # Remove large files before rewriting history
    rewrite_git_history(local_path)
    lfs(local_path)
    github_origin = get_github_origin(gh_repo)

    # Unarchive the repo if it is archived
    unarchive_github_repo(gh_repo)
    push(github_origin, local_path)
    print(f"pushed to {github_origin}")
    archive_github_repo(gh_repo)
    print("Archived GH repo")
    delete(local_path)
    print("deleted local folder")
    print(f"New GitHub URL: {github_origin}")
    return last_create_time

if __name__ == "__main__":
    repos = get_bitbucket_repos()
    last_create_time = time.time()
    for repo in tqdm(repos):
        last_create_time = migrate(*repo, last_create_time)
