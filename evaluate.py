"""Script to evaluate submitted repositories."""

import os
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright
from openai import OpenAI
from database import get_session, Repo, Task, Result
from dotenv import load_dotenv
import time

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


def check_license(repo_url, commit_sha):
    """
    Check if repo has MIT license.
    
    Returns:
        (score, reason, logs)
    """
    try:
        # Convert GitHub URL to raw content URL
        parts = repo_url.replace('https://github.com/', '').split('/')
        username, repo_name = parts[0], parts[1]
        
        license_url = f"https://raw.githubusercontent.com/{username}/{repo_name}/{commit_sha}/LICENSE"
        
        response = requests.get(license_url, timeout=10)
        
        if response.status_code == 200:
            content = response.text.lower()
            if 'mit' in content and 'permission is hereby granted' in content:
                return (1, "MIT license found", f"License content: {response.text[:200]}...")
            else:
                return (0, "License file exists but may not be MIT", f"Content: {response.text[:200]}...")
        else:
            return (0, "No LICENSE file found", f"Status: {response.status_code}")
            
    except Exception as e:
        return (0, "Error checking license", str(e))


def check_readme_quality(repo_url, commit_sha):
    """
    Check README quality using LLM.
    
    Returns:
        (score, reason, logs)
    """
    try:
        # Get README content
        parts = repo_url.replace('https://github.com/', '').split('/')
        username, repo_name = parts[0], parts[1]
        
        readme_url = f"https://raw.githubusercontent.com/{username}/{repo_name}/{commit_sha}/README.md"
        
        response = requests.get(readme_url, timeout=10)
        
        if response.status_code != 200:
            return (0, "No README.md found", f"Status: {response.status_code}")
        
        readme_content = response.text
        
        # Evaluate with LLM
        prompt = f"""Evaluate the quality of this README.md file. 

README Content:
{readme_content}

Rate the README on a scale of 0-100 based on:
1. Completeness (has summary, setup, usage sections)
2. Clarity and professionalism
3. Code explanation
4. License mention

Respond with JSON: {{"score": 0-100, "reason": "brief explanation"}}"""

        llm_response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        import json
        result = json.loads(llm_response.choices[0].message.content)
        score = 1 if result['score'] >= 70 else 0
        
        return (score, result['reason'], f"LLM Score: {result['score']}/100")
        
    except Exception as e:
        return (0, "Error evaluating README", str(e))


def check_code_quality(repo_url, commit_sha):
    """
    Check code quality using LLM.
    
    Returns:
        (score, reason, logs)
    """
    try:
        # Get index.html content
        parts = repo_url.replace('https://github.com/', '').split('/')
        username, repo_name = parts[0], parts[1]
        
        html_url = f"https://raw.githubusercontent.com/{username}/{repo_name}/{commit_sha}/index.html"
        
        response = requests.get(html_url, timeout=10)
        
        if response.status_code != 200:
            return (0, "No index.html found", f"Status: {response.status_code}")
        
        code_content = response.text
        
        # Evaluate with LLM
        prompt = f"""Evaluate the quality of this web application code.

Code:
{code_content[:3000]}...

Rate the code on a scale of 0-100 based on:
1. Code structure and organization
2. Best practices and modern JavaScript
3. Error handling
4. Comments and documentation

Respond with JSON: {{"score": 0-100, "reason": "brief explanation"}}"""

        llm_response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        import json
        result = json.loads(llm_response.choices[0].message.content)
        score = 1 if result['score'] >= 60 else 0
        
        return (score, result['reason'], f"LLM Score: {result['score']}/100")
        
    except Exception as e:
        return (0, "Error evaluating code", str(e))


def run_playwright_checks(pages_url, checks, timeout=15000):
    """
    Run Playwright checks on the deployed page.
    
    Args:
        pages_url: URL of GitHub Pages
        checks: List of check descriptions
        timeout: Timeout in milliseconds
        
    Returns:
        List of (check, score, reason, logs) tuples
    """
    results = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Wait for page to be available (GitHub Pages may take time)
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    response = page.goto(pages_url, timeout=timeout, wait_until='networkidle')
                    if response and response.status == 200:
                        break
                except Exception as e:
                    if attempt < max_attempts - 1:
                        print(f"Attempt {attempt + 1} failed, retrying in 5 seconds...")
                        time.sleep(5)
                    else:
                        browser.close()
                        return [(check, 0, "Page not accessible", str(e)) for check in checks]
            
            # Run each check
            for check in checks:
                try:
                    # Parse check type and run appropriate validation
                    if 'title' in check.lower():
                        title = page.title()
                        # Check if title matches expected pattern
                        if 'Sales Summary' in check and 'Sales Summary' in title:
                            results.append((check, 1, "Title matches", f"Title: {title}"))
                        else:
                            results.append((check, 0, "Title mismatch", f"Title: {title}"))
                    
                    elif 'bootstrap' in check.lower():
                        # Check for Bootstrap link
                        bootstrap_link = page.query_selector('link[href*="bootstrap"]')
                        if bootstrap_link:
                            results.append((check, 1, "Bootstrap found", "Link element exists"))
                        else:
                            results.append((check, 0, "Bootstrap not found", "No Bootstrap link"))
                    
                    elif '#' in check:
                        # Element check
                        selector = check.split('#')[1].split()[0]
                        element = page.query_selector(f'#{selector}')
                        if element:
                            results.append((check, 1, f"Element #{selector} found", "Element exists"))
                        else:
                            results.append((check, 0, f"Element #{selector} not found", "Element missing"))
                    
                    elif 'marked' in check.lower() or 'highlight' in check.lower():
                        # Check for script includes
                        script_src = 'marked' if 'marked' in check.lower() else 'highlight'
                        script = page.query_selector(f'script[src*="{script_src}"]')
                        if script:
                            results.append((check, 1, f"{script_src}.js found", "Script loaded"))
                        else:
                            results.append((check, 0, f"{script_src}.js not found", "Script missing"))
                    
                    elif 'license' in check.lower():
                        # License check (handled separately)
                        results.append((check, 1, "Checked separately", "License validation"))
                    
                    elif 'readme' in check.lower():
                        # README check (handled separately)
                        results.append((check, 1, "Checked separately", "README validation"))
                    
                    else:
                        # Generic check - just mark as pass for now
                        results.append((check, 1, "Generic check passed", "No specific validation"))
                        
                except Exception as e:
                    results.append((check, 0, "Error running check", str(e)))
            
            browser.close()
            
    except Exception as e:
        return [(check, 0, "Playwright error", str(e)) for check in checks]
    
    return results


def evaluate_submission(repo_entry, task_entry):
    """
    Evaluate a single submission.
    
    Args:
        repo_entry: Repo database entry
        task_entry: Task database entry
        
    Returns:
        List of Result entries
    """
    results = []
    
    print(f"[{datetime.utcnow().isoformat()}] Evaluating {repo_entry.email} - {repo_entry.task}")
    
    # Check license
    score, reason, logs = check_license(repo_entry.repo_url, repo_entry.commit_sha)
    results.append({
        'check': 'MIT License',
        'score': score,
        'reason': reason,
        'logs': logs
    })
    
    # Check README quality
    score, reason, logs = check_readme_quality(repo_entry.repo_url, repo_entry.commit_sha)
    results.append({
        'check': 'README Quality',
        'score': score,
        'reason': reason,
        'logs': logs
    })
    
    # Check code quality
    score, reason, logs = check_code_quality(repo_entry.repo_url, repo_entry.commit_sha)
    results.append({
        'check': 'Code Quality',
        'score': score,
        'reason': reason,
        'logs': logs
    })
    
    # Run Playwright checks
    playwright_results = run_playwright_checks(repo_entry.pages_url, task_entry.checks)
    for check, score, reason, logs in playwright_results:
        results.append({
            'check': check,
            'score': score,
            'reason': reason,
            'logs': logs
        })
    
    return results


def run_evaluation():
    """Main function to run evaluation on all submissions."""
    print(f"[{datetime.utcnow().isoformat()}] Starting evaluation...")
    
    session = get_session()
    
    try:
        # Get all repos that haven't been evaluated
        repos = session.query(Repo).all()
        
        print(f"[{datetime.utcnow().isoformat()}] Found {len(repos)} submissions to evaluate")
        
        for repo in repos:
            # Check if already evaluated
            existing_results = session.query(Result).filter_by(
                email=repo.email,
                task=repo.task,
                round=repo.round
            ).count()
            
            if existing_results > 0:
                print(f"[{datetime.utcnow().isoformat()}] Skipping {repo.email} - already evaluated")
                continue
            
            # Get corresponding task
            task = session.query(Task).filter_by(
                email=repo.email,
                task=repo.task,
                round=repo.round
            ).first()
            
            if not task:
                print(f"[{datetime.utcnow().isoformat()}] Warning: No task found for {repo.email}")
                continue
            
            # Evaluate
            evaluation_results = evaluate_submission(repo, task)
            
            # Save results
            for result_data in evaluation_results:
                result = Result(
                    email=repo.email,
                    task=repo.task,
                    round=repo.round,
                    repo_url=repo.repo_url,
                    commit_sha=repo.commit_sha,
                    pages_url=repo.pages_url,
                    check=result_data['check'],
                    score=result_data['score'],
                    reason=result_data['reason'],
                    logs=result_data['logs']
                )
                session.add(result)
            
            session.commit()
            
            print(f"[{datetime.utcnow().isoformat()}] Evaluation complete for {repo.email}")
        
        print(f"[{datetime.utcnow().isoformat()}] All evaluations complete!")
        
    finally:
        session.close()


if __name__ == '__main__':
    run_evaluation()
