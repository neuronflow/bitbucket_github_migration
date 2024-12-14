# Bitbucket to GitHub Migration Script
> WARNING: use at your own risk!

This script automates the process of migrating repositories from private Bitbucket to GitHub accounts. It clones the repositories from Bitbucket, rewrites the Git history, and pushes them to GitHub.


## Inspiration
This script for organization accounts served as the inspiration:
https://medium.com/@marcelkornblum/moving-from-bitbucket-to-github-188f0e9c6426

## Prerequisites

- Python 3.12
- `pip` (Python package installer)
- `git`
- `python-dotenv` package

## Installation

1. Clone the repository

2. Install the required Python packages:

    ```sh
    pip install -r requirements.txt
    ```

3. Create a [.env](http://_vscodecontentref_/1) file in the root directory of the project and add your Bitbucket and GitHub credentials:

    ```env
    BITBUCKET_USER=your_bitbucket_username
    BITBUCKET_PASS=your_bitbucket_password
    BITBUCKET_ORG=your_bitbucket_organization
    GITHUB_USER=your_github_username
    GITHUB_ACCESS_TOKEN=your_github_access_token
    GITHUB_ORG=your_github_organization
    ```

## Usage

First create your API keys on Bitbucket and GitHub and put them in you `.env` file then:

1. Run the migration script:

    ```sh
    python migrate.py
    ```

2. The script will:
    - Load the credentials from the [.env](http://_vscodecontentref_/2) file.
    - Fetch the list of repositories from Bitbucket.
    - Clone each repository to a local directory.
    - Rewrite the Git history.
    - Push the repository to GitHub.
    - Print the new GitHub URL for each repository.

## Notes

- Ensure that your [.env](http://_vscodecontentref_/3) file is not included in version control to keep your credentials secure.
- The script uses the `tqdm` library to display progress bars for long-running operations.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
