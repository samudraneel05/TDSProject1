"""Task templates for code generation challenges."""

import random
import base64
import json


def get_task_templates():
    """Return list of task templates."""
    return [
        {
            "id": "sum-of-sales",
            "brief": "Publish a single-page site that fetches data.csv from attachments, sums its sales column, sets the title to 'Sales Summary {seed}', displays the total inside #total-sales, and loads Bootstrap 5 from jsdelivr.",
            "attachments_generator": generate_sales_csv,
            "checks": [
                "Repo has MIT license",
                "README.md is professional",
                "Page title matches 'Sales Summary {seed}'",
                "Bootstrap 5 is loaded from CDN",
                "#total-sales element displays correct sum"
            ],
            "round2_options": [
                {
                    "brief": "Add a Bootstrap table #product-sales that lists each product with its total sales and keeps #total-sales accurate after render.",
                    "checks": [
                        "#product-sales table has at least 1 row",
                        "Sum of product sales matches #total-sales"
                    ]
                },
                {
                    "brief": "Introduce a currency select #currency-picker that converts the computed total using rates.json from attachments and mirrors the active currency inside #total-currency.",
                    "attachments_generator": generate_currency_rates,
                    "checks": [
                        "#currency-picker has USD option",
                        "#total-currency element exists"
                    ]
                }
            ]
        },
        {
            "id": "markdown-to-html",
            "brief": "Publish a static page that converts input.md from attachments to HTML with marked.js, renders it inside #markdown-output, and loads highlight.js for code blocks.",
            "attachments_generator": generate_markdown_file,
            "checks": [
                "Repo has MIT license",
                "README.md is professional",
                "marked.js is loaded",
                "highlight.js is loaded",
                "#markdown-output contains rendered HTML"
            ],
            "round2_options": [
                {
                    "brief": "Add tabs #markdown-tabs that switch between rendered HTML in #markdown-output and the original Markdown in #markdown-source while keeping content in sync.",
                    "checks": [
                        "#markdown-tabs has at least 2 buttons",
                        "#markdown-source displays original markdown"
                    ]
                },
                {
                    "brief": "Support loading Markdown from a ?url= parameter when present and fall back to the attachment otherwise, showing the active source in #markdown-source-label.",
                    "checks": [
                        "#markdown-source-label displays source info",
                        "Code includes fetch() for URL loading"
                    ]
                }
            ]
        },
        {
            "id": "github-user-info",
            "brief": "Publish a Bootstrap page with form id='github-user-{seed}' that fetches a GitHub username, optionally uses ?token=, and displays the account creation date in YYYY-MM-DD UTC inside #github-created-at.",
            "attachments_generator": None,
            "checks": [
                "Repo has MIT license",
                "README.md is professional",
                "Form with id 'github-user-{seed}' exists",
                "#github-created-at displays date",
                "Code calls GitHub API"
            ],
            "round2_options": [
                {
                    "brief": "Show an aria-live alert #github-status that reports when a lookup starts, succeeds, or fails.",
                    "checks": [
                        "#github-status has aria-live='polite'",
                        "Status messages are shown"
                    ]
                },
                {
                    "brief": "Display the account age in whole years inside #github-account-age alongside the creation date.",
                    "checks": [
                        "#github-account-age displays numeric value",
                        "Text includes 'years'"
                    ]
                }
            ]
        }
    ]


def generate_sales_csv(seed):
    """Generate sample sales CSV data."""
    random.seed(seed)
    
    products = ['Widget A', 'Widget B', 'Widget C', 'Widget D', 'Widget E']
    csv_lines = ['product,sales']
    
    total = 0
    for product in products:
        sales = round(random.uniform(100, 1000), 2)
        total += sales
        csv_lines.append(f"{product},{sales}")
    
    csv_content = '\n'.join(csv_lines)
    encoded = base64.b64encode(csv_content.encode()).decode()
    
    return {
        'content': csv_content,
        'encoded': f"data:text/csv;base64,{encoded}",
        'total': total
    }


def generate_markdown_file(seed):
    """Generate sample markdown file."""
    random.seed(seed)
    
    titles = ['Introduction', 'Overview', 'Getting Started', 'User Guide']
    title = random.choice(titles)
    
    markdown_content = f"""# {title}

This is a sample markdown document generated for testing.

## Features

- **Bold text** for emphasis
- *Italic text* for subtle emphasis
- `Code snippets` inline

## Code Block

```python
def hello_world():
    print("Hello, World!")
    return True
```

## Lists

1. First item
2. Second item
3. Third item

## Conclusion

This demonstrates markdown rendering capabilities.
"""
    
    encoded = base64.b64encode(markdown_content.encode()).decode()
    
    return {
        'content': markdown_content,
        'encoded': f"data:text/markdown;base64,{encoded}"
    }


def generate_currency_rates(seed):
    """Generate currency conversion rates."""
    random.seed(seed)
    
    rates = {
        "USD": 1.0,
        "EUR": round(random.uniform(0.85, 0.95), 4),
        "GBP": round(random.uniform(0.75, 0.85), 4),
        "JPY": round(random.uniform(110, 150), 4),
        "INR": round(random.uniform(70, 85), 4)
    }
    
    json_content = json.dumps(rates, indent=2)
    encoded = base64.b64encode(json_content.encode()).decode()
    
    return {
        'content': json_content,
        'encoded': f"data:application/json;base64,{encoded}",
        'rates': rates
    }


def generate_task_data(templates, seed, round_num=1):
    """
    Generate task data for a student.
    
    Args:
        templates: List of task templates
        seed: Seed for randomization
        round_num: Round number (1 or 2)
        
    Returns:
        Dict with task details
    """
    # Select random template
    random.seed(seed)
    template = random.choice(templates)
    
    if round_num == 1:
        # Generate round 1 task
        brief = template['brief'].replace('{seed}', str(abs(hash(seed)) % 10000))
        checks = [check.replace('{seed}', str(abs(hash(seed)) % 10000)) for check in template['checks']]
        
        # Generate attachments if needed
        attachments = []
        if template['attachments_generator']:
            attachment_data = template['attachments_generator'](seed)
            
            # Determine filename
            if 'csv' in template['brief'].lower():
                filename = 'data.csv'
            elif 'markdown' in template['brief'].lower():
                filename = 'input.md'
            elif 'json' in template['brief'].lower():
                filename = 'rates.json'
            else:
                filename = 'data.txt'
            
            attachments.append({
                'name': filename,
                'url': attachment_data['encoded']
            })
        
        return {
            'template_id': template['id'],
            'brief': brief,
            'checks': checks,
            'attachments': attachments
        }
    
    else:
        # Generate round 2 task
        round2_option = random.choice(template['round2_options'])
        brief = round2_option['brief'].replace('{seed}', str(abs(hash(seed)) % 10000))
        checks = [check.replace('{seed}', str(abs(hash(seed)) % 10000)) for check in round2_option['checks']]
        
        # Generate attachments if needed
        attachments = []
        if 'attachments_generator' in round2_option:
            attachment_data = round2_option['attachments_generator'](seed)
            
            if 'json' in round2_option['brief'].lower():
                filename = 'rates.json'
            else:
                filename = 'data.txt'
            
            attachments.append({
                'name': filename,
                'url': attachment_data['encoded']
            })
        
        return {
            'template_id': template['id'],
            'brief': brief,
            'checks': checks,
            'attachments': attachments
        }
