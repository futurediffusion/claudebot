import os
import subprocess
from datetime import datetime, timedelta
import json

def get_git_activity(repo_path):
    try:
        since = (datetime.now() - timedelta(days=1)).isoformat()
        cmd = ['git', '-C', repo_path, 'log', f'--since={since}', '--pretty=format:%s']
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return [c for f in result.stdout.strip().split('\n') if (c := f.strip())]
    except: return []

def get_creative_activity(path):
    activity = {"images": 0, "models": 0}
    if not os.path.exists(path): return activity
    exts = {'.jpg', '.png', '.webp', '.jpeg', '.safetensors', '.ckpt'}
    now = datetime.now()
    for root, _, files in os.walk(path):
        for name in files:
            ext = os.path.splitext(name)[1].lower()
            if ext in exts:
                try:
                    if now - datetime.fromtimestamp(os.path.getmtime(os.path.join(root, name))) < timedelta(days=1):
                        if ext in {'.safetensors', '.ckpt'}: activity['models'] += 1
                        else: activity['images'] += 1
                except: continue
    return activity

def get_finance_summary():
    path = 'D:\\IA\\CODE\\claudebot\\personal_HUB\\expense_tracker\\data\\finance.json'
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                today = datetime.now().strftime('%Y-%m-%d')
                income = sum(t['amount'] for t in data.get('transactions', []) if t['date'] == today and t['type'] == 'income')
                return {"income_today": income}
        except: return {"income_today": 0}
    return {"income_today": 0}

def main():
    workspace_root = 'D:\\IA\\CODE\\claudebot'
    workspace_roots = ['D:\\IA\\CODE', 'D:\\CODE']
    real_workspace = 'D:\\WILLY\\WORKSPACE\\NEWORKSPACE'
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_commits": 0,
        "active_projects": [],
        "creative_work": get_creative_activity(real_workspace),
        "finance": get_finance_summary(),
        "files_touched": 0
    }

    tracked_paths = set()
    core_hubs = {
        '⭐ ClaudeBot System': workspace_root,
        '⭐ Money Maker HUB': os.path.join(workspace_root, 'personal_HUB', 'money_maker_hub'),
    }

    # Procesar CORE
    for name, path in core_hubs.items():
        if os.path.exists(path):
            commits = get_git_activity(path)
            if commits:
                report["active_projects"].append({"name": name, "commits": commits, "files_count": 0})
                report["total_commits"] += len(commits)
                tracked_paths.add(os.path.normpath(path))

    # Procesar FLOTA
    for root in workspace_roots:
        if not os.path.exists(root): continue
        for project_name in os.listdir(root):
            p_path = os.path.join(root, project_name)
            if os.path.isdir(p_path) and not project_name.startswith('.') and os.path.normpath(p_path) not in tracked_paths:
                commits = get_git_activity(p_path)
                if commits:
                    report["active_projects"].append({"name": project_name, "commits": commits})
                    report["total_commits"] += len(commits)

    with open(os.path.join(workspace_root, 'life_logs', 'project_activity.json'), 'w') as f:
        json.dump(report, f, indent=2)
    print("Bridge: Sensor total actualizado (Código, Creativo, Finanzas).")

if __name__ == "__main__":
    main()
