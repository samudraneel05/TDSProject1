# TDS Project 1: LLM Code Deployment System

An automated system for building, deploying, and evaluating student-generated web applications using LLMs and GitHub Pages.

## Overview

This project implements a comprehensive workflow where:

1. **Students** host an API endpoint that receives app requirements, uses LLMs to generate code, deploys to GitHub Pages, and notifies an evaluation API
2. **Instructors** send task requests, receive submissions, and run automated evaluations using static analysis, LLM checks, and Playwright tests

## Quick Start

1. **Setup**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   cp .env.example .env
   # Edit .env with your API keys
   ```

2. **Initialize Database**
   ```bash
   python database.py
   ```

3. **Run Student API**
   ```bash
   python app.py
   ```

4. **Run Evaluation API** (separate terminal)
   ```bash
   python evaluation_api.py
   ```

## Project Structure

- **Student Side**: `app.py`, `app_generator.py`, `github_handler.py`, `evaluation_notifier.py`
- **Instructor Side**: `evaluation_api.py`, `round1.py`, `round2.py`, `evaluate.py`, `task_templates.py`
- **Shared**: `database.py`, `requirements.txt`

## Key Features

- 🤖 **LLM-Assisted Code Generation** - Uses OpenAI GPT-4
- 🚀 **Automated GitHub Deployment** - Creates repos and enables Pages
- 🔍 **Multi-Layer Evaluation** - License, README, code quality, Playwright tests
- 🔄 **Round-Based System** - Initial build + revision tasks
- 📊 **Database Tracking** - PostgreSQL/SQLite

## Environment Variables

Required in `.env`:
- `OPENAI_API_KEY` - OpenAI API key
- `GITHUB_TOKEN` - GitHub personal access token
- `STUDENT_SECRET` - Your secret from Google Form
- `DATABASE_URL` - Database connection (defaults to SQLite)
- `API_BASE_URL` - Your deployment URL

## Usage

### For Students
1. Deploy your API endpoint to a cloud service
2. Submit your endpoint URL and secret via Google Form
3. Receive tasks automatically, generate and deploy apps
4. System notifies evaluation API with results

### For Instructors
1. Start evaluation API: `python evaluation_api.py`
2. Send Round 1 tasks: `python round1.py submissions.csv`
3. Run evaluations: `python evaluate.py`
4. Send Round 2 tasks: `python round2.py`

## License

MIT License

## Credits

Developed for IIT Madras Tools in Data Science course.
