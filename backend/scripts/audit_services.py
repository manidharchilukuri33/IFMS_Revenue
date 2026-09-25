import glob, os, re, json

def inspect_services():
    services = sorted(glob.glob('backend/app/services/*.py'))
    svc_data = {}
    for s in services:
        s_name = os.path.basename(s)
        with open(s, 'r', encoding='utf-8') as f:
            code = f.read()
            
        # Find imports of models
        models = re.findall(r'from\s+app\.models\.[a-zA-Z0-9_]+\s+import\s+([^\n]+)', code)
        model_list = []
        for m in models:
            for item in m.split(','):
                item = item.strip()
                if item and not item.startswith('(') and not item.startswith(')'):
                    model_list.append(item)
                    
        # Find stored procedure calls (sp_rev_... or CALL ...)
        sp_calls = re.findall(r'(?:CALL|call|SELECT|select)\s+([a-zA-Z0-9_\.]*sp_rev_[a-zA-Z0-9_]+|[a-zA-Z0-9_\.]*fn_rev_[a-zA-Z0-9_]+)', code, re.IGNORECASE)
        sp_calls += re.findall(r'text\(["\'](?:CALL|call)\s+([a-zA-Z0-9_\.]+)', code)
        
        # Find methods
        method_matches = re.finditer(r'(?:async\s+def|def)\s+([a-zA-Z0-9_]+)\((.*?)\):', code)
        methods = []
        for m in method_matches:
            m_name = m.group(1)
            params = m.group(2).replace('\n', ' ')
            
            # search method body for SQL operations
            start_pos = m.end()
            next_m = re.search(r'\n    (?:async\s+def|def)\s+', code[start_pos:])
            body = code[start_pos:start_pos + next_m.start()] if next_m else code[start_pos:start_pos+4000]
            
            has_insert = 'db.add' in body or 'INSERT INTO' in body or 'insert(' in body
            has_update = 'UPDATE' in body or 'update(' in body or 'commit()' in body and ('=' in body)
            has_delete = 'db.delete' in body or 'DELETE' in body or 'delete(' in body
            has_select = 'select(' in body or 'SELECT' in body or 'db.get' in body
            
            methods.append({
                'name': m_name,
                'params': params,
                'ops': {
                    'SELECT': has_select,
                    'INSERT': has_insert,
                    'UPDATE': has_update,
                    'DELETE': has_delete
                },
                'body_summary': body[:200].replace('\n', ' ')
            })
            
        svc_data[s_name] = {
            'models_imported': sorted(list(set(model_list))),
            'procedure_calls': sorted(list(set(sp_calls))),
            'methods': methods
        }
    return svc_data

if __name__ == '__main__':
    data = inspect_services()
    with open('backend/scripts/services_inspection.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"Dumped {len(data)} services to backend/scripts/services_inspection.json")
