"""GitHub repository creation and management."""

import os
import time
from github import Github, GithubException
from dotenv import load_dotenv

load_dotenv()

# Initialize GitHub client
gh = Github(os.getenv('GITHUB_TOKEN'))


def create_repo(repo_name, description="Auto-generated repository"):
    """
    Create a new GitHub repository.
    
    Args:
        repo_name: Name of the repository
        description: Repository description
        
    Returns:
        Repository object
    """
    try:
        user = gh.get_user()
        
        try:
            existing_repo = user.get_repo(repo_name)
            print(f"Repository {repo_name} already exists, deleting...")
            existing_repo.delete()
            time.sleep(2)  # Wait for deletion to complete
        except GithubException:
            pass
        
        # Create new repository
        repo = user.create_repo(
            name=repo_name,
            description=description,
            private=False,
            auto_init=False,
            has_issues=True,
            has_wiki=False,
            has_downloads=True
        )
        
        print(f"Created repository: {repo.html_url}")
        time.sleep(2)  # Wait for repo to be fully created
        
        return repo
        
    except GithubException as e:
        print(f"Error creating repository: {str(e)}")
        raise


def push_to_repo(repo, files):
    """
    Push files to repository.
    
    Args:
        repo: Repository object
        files: Dict of {filename: content}
        
    Returns:
        Commit SHA
    """
    try:
        # Create files in repository
        for filename, content in files.items():
            try:
                repo.create_file(
                    path=filename,
                    message=f"Add {filename}",
                    content=content,
                    branch="main"
                )
                print(f"Created file: {filename}")
            except GithubException as e:
                if e.status == 422:  # File already exists
                    # Update existing file
                    contents = repo.get_contents(filename)
                    repo.update_file(
                        path=filename,
                        message=f"Update {filename}",
                        content=content,
                        sha=contents.sha,
                        branch="main"
                    )
                    print(f"Updated file: {filename}")
                else:
                    raise
        
        # Get latest commit SHA
        commits = repo.get_commits()
        latest_commit = list(commits)[0]
        
        return latest_commit.sha
        
    except GithubException as e:
        print(f"Error pushing to repository: {str(e)}")
        raise


def enable_github_pages(repo):
    """
    Enable GitHub Pages for the repository.
    
    Args:
        repo: Repository object
        
    Returns:
        Pages URL
    """
    try:
        username = gh.get_user().login
        repo_name = repo.name
        
        # Try to enable Pages via API
        try:
            repo.create_git_ref(ref='refs/heads/gh-pages', sha=repo.get_branch('main').commit.sha)
        except GithubException:
            pass  # Branch might already exist or Pages might already be enabled
        
        # The Pages URL format
        pages_url = f"https://{username.lower()}.github.io/{repo_name}/"
        
        print(f"GitHub Pages should be available at: {pages_url}")
        print("Note: It may take a few minutes for the site to become available.")
        
        return pages_url
        
    except Exception as e:
        print(f"Error enabling GitHub Pages: {str(e)}")
        # Return expected URL anyway
        username = gh.get_user().login
        return f"https://{username.lower()}.github.io/{repo.name}/"


def update_repo(repo_name, files):
    """
    Update existing repository with new files.
    
    Args:
        repo_name: Name of the repository
        files: Dict of {filename: content}
        
    Returns:
        New commit SHA
    """
    try:
        user = gh.get_user()
        repo = user.get_repo(repo_name)
        
        # Update each file
        for filename, content in files.items():
            try:
                # Try to get existing file
                file_content = repo.get_contents(filename)
                repo.update_file(
                    path=filename,
                    message=f"Update {filename}",
                    content=content,
                    sha=file_content.sha,
                    branch="main"
                )
                print(f"Updated file: {filename}")
            except GithubException as e:
                if e.status == 404:  # File doesn't exist
                    repo.create_file(
                        path=filename,
                        message=f"Add {filename}",
                        content=content,
                        branch="main"
                    )
                    print(f"Created file: {filename}")
                else:
                    raise
        
        # Get latest commit SHA
        commits = repo.get_commits()
        latest_commit = list(commits)[0]
        
        return latest_commit.sha
        
    except GithubException as e:
        print(f"Error updating repository: {str(e)}")
        raise


def get_repo_info(repo_name):
    """
    Get information about a repository.
    
    Args:
        repo_name: Name of the repository
        
    Returns:
        Dict with repo information
    """
    try:
        user = gh.get_user()
        repo = user.get_repo(repo_name)
        
        return {
            'name': repo.name,
            'url': repo.html_url,
            'created_at': repo.created_at,
            'updated_at': repo.updated_at,
            'default_branch': repo.default_branch
        }
        
    except GithubException as e:
        print(f"Error getting repository info: {str(e)}")
        return None
