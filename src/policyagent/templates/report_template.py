"""Default HTML report template."""

REPORT_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Policy Report - {{ policy_name }}</title>
    <style>
        :root {
            --primary: #2563eb; --success: #16a34a; --warning: #ca8a04; --danger: #dc2626;
            --gray-100: #f3f4f6; --gray-200: #e5e7eb; --gray-700: #374151; --gray-900: #111827;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6; color: var(--gray-900); max-width: 1200px;
            margin: 0 auto; padding: 2rem; background: var(--gray-100);
        }
        .header {
            background: white; padding: 2rem; border-radius: 8px;
            margin-bottom: 2rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        h1 { color: var(--primary); margin: 0 0 0.5rem 0; }
        .meta { color: var(--gray-700); font-size: 0.9rem; }
        .rule {
            background: white; padding: 1.5rem; border-radius: 8px;
            margin-bottom: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .rule h2 { margin: 0 0 1rem 0; display: flex; align-items: center; gap: 0.5rem; }
        .badge {
            display: inline-block; padding: 0.25rem 0.75rem; border-radius: 9999px;
            font-size: 0.75rem; font-weight: 600; text-transform: uppercase;
        }
        .badge-mutual_exclusion { background: #dbeafe; color: #1d4ed8; }
        .badge-overutilization { background: #fef3c7; color: #92400e; }
        .badge-service_not_covered { background: #fee2e2; color: #991b1b; }
        .confidence { display: flex; align-items: center; gap: 0.5rem; margin: 1rem 0; }
        .confidence-bar { flex: 1; height: 8px; background: var(--gray-200); border-radius: 4px; overflow: hidden; }
        .confidence-fill { height: 100%; background: var(--primary); transition: width 0.3s ease; }
        .sql-block {
            background: var(--gray-900); color: #e5e7eb; padding: 1rem; border-radius: 4px;
            overflow-x: auto; font-family: 'Monaco', 'Menlo', monospace; font-size: 0.875rem; white-space: pre;
        }
        .sources { margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--gray-200); }
        .sources h3 { font-size: 0.875rem; color: var(--gray-700); margin: 0 0 0.5rem 0; }
        .sources ul { margin: 0; padding-left: 1.5rem; font-size: 0.875rem; }
        .sources a { color: var(--primary); }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ policy_name }}</h1>
        <p class="meta">Generated: {{ generated_at }}<br>Total Rules: {{ rules | length }}</p>
    </div>
    {% for rule in rules %}
    <div class="rule">
        <h2>{{ rule.name }}<span class="badge badge-{{ rule.classification }}">{{ rule.classification | replace('_', ' ') }}</span></h2>
        <p>{{ rule.description }}</p>
        <div class="confidence">
            <span>Confidence:</span>
            <div class="confidence-bar"><div class="confidence-fill" style="width: {{ rule.confidence }}%"></div></div>
            <span>{{ rule.confidence }}%</span>
        </div>
        <h3>SQL Implementation</h3>
        <div class="sql-block">{{ rule.sql }}</div>
        {% if rule.sources %}
        <div class="sources">
            <h3>Validation Sources</h3>
            <ul>{% for source in rule.sources %}<li><a href="{{ source.url }}" target="_blank">{{ source.title }}</a></li>{% endfor %}</ul>
        </div>
        {% endif %}
    </div>
    {% endfor %}
</body>
</html>'''
