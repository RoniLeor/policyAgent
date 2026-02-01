"""Default HTML report template."""

REPORT_TEMPLATE = """<!DOCTYPE html>
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
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6; color: var(--gray-900); max-width: 1200px; margin: 0 auto; padding: 2rem; background: var(--gray-100); }
        .header { background: white; padding: 2rem; border-radius: 8px; margin-bottom: 2rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        h1 { color: var(--primary); margin: 0 0 0.5rem 0; }
        .meta { color: var(--gray-700); font-size: 0.9rem; }
        .stats { display: flex; gap: 2rem; margin-top: 1rem; }
        .stat { background: var(--gray-100); padding: 0.5rem 1rem; border-radius: 4px; }
        .stat-value { font-size: 1.5rem; font-weight: bold; color: var(--primary); }
        .stat-label { font-size: 0.75rem; color: var(--gray-700); }
        .rule { background: white; padding: 1.5rem; border-radius: 8px; margin-bottom: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .rule h2 { margin: 0 0 1rem 0; display: flex; align-items: center; gap: 0.5rem; }
        .badge { display: inline-block; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }
        .badge-mutual_exclusion { background: #dbeafe; color: #1d4ed8; }
        .badge-overutilization { background: #fef3c7; color: #92400e; }
        .badge-service_not_covered { background: #fee2e2; color: #991b1b; }
        .confidence { display: flex; align-items: center; gap: 0.5rem; margin: 1rem 0; }
        .confidence-bar { flex: 1; height: 8px; background: var(--gray-200); border-radius: 4px; overflow: hidden; max-width: 200px; }
        .confidence-fill { height: 100%; background: var(--primary); }
        .sql-block { background: var(--gray-900); color: #e5e7eb; padding: 1rem; border-radius: 4px; overflow-x: auto;
            font-family: 'Monaco', 'Menlo', monospace; font-size: 0.875rem; white-space: pre; }
        .sources { margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--gray-200); }
        .sources h3 { font-size: 0.875rem; color: var(--gray-700); margin: 0 0 0.5rem 0; }
        .sources ul { margin: 0; padding-left: 1.5rem; font-size: 0.875rem; }
        .sources a { color: var(--primary); }
        .violations { margin-top: 1rem; padding: 1rem; background: #fef2f2; border-radius: 4px; border-left: 4px solid var(--danger); }
        .violations h3 { margin: 0 0 0.5rem 0; color: var(--danger); font-size: 0.9rem; }
        .violations-table { width: 100%; border-collapse: collapse; font-size: 0.8rem; margin-top: 0.5rem; }
        .violations-table th { background: var(--gray-200); padding: 0.5rem; text-align: left; border-bottom: 1px solid var(--gray-700); }
        .violations-table td { padding: 0.5rem; border-bottom: 1px solid var(--gray-200); }
        .no-violations { color: var(--success); padding: 0.5rem; background: #f0fdf4; border-radius: 4px; margin-top: 1rem; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ policy_name }}</h1>
        <p class="meta">Generated: {{ generated_at }}</p>
        <div class="stats">
            <div class="stat"><div class="stat-value">{{ rules | length }}</div><div class="stat-label">Rules</div></div>
            <div class="stat"><div class="stat-value">{{ total_violations }}</div><div class="stat-label">Violations Found</div></div>
            <div class="stat"><div class="stat-value">{{ total_pages }}</div><div class="stat-label">Pages</div></div>
        </div>
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
        {% if rule.query_executed %}
            {% if rule.violation_count > 0 %}
            <div class="violations">
                <h3>⚠️ {{ rule.violation_count }} Violation(s) Found</h3>
                <table class="violations-table">
                    <thead><tr>{% for col in rule.columns %}<th>{{ col }}</th>{% endfor %}</tr></thead>
                    <tbody>
                    {% for row in rule.violations %}
                        <tr>{% for col in rule.columns %}<td>{{ row[col] }}</td>{% endfor %}</tr>
                    {% endfor %}
                    </tbody>
                </table>
                {% if rule.violation_count > 10 %}<p style="font-size:0.8rem;color:var(--gray-700);">Showing first 10 of {{ rule.violation_count }} violations</p>{% endif %}
            </div>
            {% else %}
            <div class="no-violations">✓ No violations found in claims database</div>
            {% endif %}
        {% endif %}
        {% if rule.sources %}
        <div class="sources">
            <h3>Validation Sources</h3>
            <ul>{% for source in rule.sources %}<li><a href="{{ source.url }}" target="_blank">{{ source.title }}</a></li>{% endfor %}</ul>
        </div>
        {% endif %}
    </div>
    {% endfor %}
</body>
</html>"""
