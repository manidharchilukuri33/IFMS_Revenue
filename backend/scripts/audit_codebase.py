import os, re, json, glob

def inspect_frontend():
    pages = sorted(glob.glob('frontend/src/pages/*.tsx'))
    page_data = {}
    for p in pages:
        p_name = os.path.basename(p)
        with open(p, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Find API calls
        api_calls = re.findall(r'api\.([a-zA-Z0-9_]+)\(', code)
        
        # Find buttons
        button_matches = re.findall(r'<button\b([^>]*)>(.*?)</button>', code, re.DOTALL)
        buttons = []
        for attrs, content in button_matches:
            # clean content
            text = re.sub(r'<[^>]+>', '', content).strip()
            # extract onClick
            onclick = re.search(r'onClick=\{([^}]+)\}', attrs)
            disabled = re.search(r'disabled=\{([^}]+)\}', attrs)
            title = re.search(r'title=["\']([^"\']+)["\']', attrs)
            buttons.append({
                'text': text[:80],
                'onClick': onclick.group(1).strip() if onclick else '',
                'disabled': disabled.group(1).strip() if disabled else '',
                'title': title.group(1).strip() if title else ''
            })
            
        # Find Forms
        form_matches = re.findall(r'<form\b([^>]*)>(.*?)</form>', code, re.DOTALL)
        forms = []
        for attrs, content in form_matches:
            onsubmit = re.search(r'onSubmit=\{([^}]+)\}', attrs)
            # Find inputs and selects
            inputs = re.findall(r'<(input|select|textarea)\b([^>]*)>', content)
            fields = []
            for tag, iattrs in inputs:
                name = re.search(r'(?:name|placeholder|value)=["\'{]([^"\'}]+)["\'}]', iattrs)
                typ = re.search(r'type=["\']([^"\']+)["\']', iattrs)
                req = 'required' in iattrs
                fields.append({
                    'tag': tag,
                    'type': typ.group(1) if typ else ('select' if tag == 'select' else 'text'),
                    'name_or_placeholder': name.group(1) if name else '',
                    'required': req
                })
            forms.append({
                'onSubmit': onsubmit.group(1).strip() if onsubmit else '',
                'fields_count': len(fields),
                'fields': fields
            })

        # Role checks
        role_checks = re.findall(r'(?:userRole|role|can)\b[^\n]+', code)
        
        page_data[p_name] = {
            'api_calls': sorted(list(set(api_calls))),
            'buttons_count': len(buttons),
            'buttons': buttons,
            'forms_count': len(forms),
            'forms': forms,
            'role_checks': role_checks[:10]
        }
    return page_data

def inspect_backend_routers():
    routers = sorted(glob.glob('backend/app/routers/*.py'))
    router_data = {}
    for r in routers:
        r_name = os.path.basename(r)
        with open(r, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # find endpoints: @router.get/post/put/delete
        endpoint_matches = re.finditer(r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']([^\)]*)\)\s*(?:@[^\n]+\s*)*async\s+def\s+([a-zA-Z0-9_]+)\((.*?)\):', code, re.DOTALL)
        endpoints = []
        for ep in endpoint_matches:
            method = ep.group(1).upper()
            path = ep.group(2)
            extra = ep.group(3)
            func_name = ep.group(4)
            params = ep.group(5).replace('\n', ' ')
            
            # extract service calls inside function body
            # find start of next func or end of file
            start_pos = ep.end()
            next_ep = re.search(r'@router\.', code[start_pos:])
            func_body = code[start_pos:start_pos + next_ep.start()] if next_ep else code[start_pos:start_pos+3000]
            
            services = re.findall(r'([A-Za-z0-9_]+Service\.[a-zA-Z0-9_]+)', func_body)
            deps = re.findall(r'require_capability\(["\']([^"\']+)["\']\)', extra)
            
            endpoints.append({
                'method': method,
                'path': path,
                'func_name': func_name,
                'capability': deps[0] if deps else 'None',
                'service_calls': sorted(list(set(services)))
            })
        router_data[r_name] = endpoints
    return router_data

if __name__ == '__main__':
    fe = inspect_frontend()
    with open('backend/scripts/frontend_inspection.json', 'w', encoding='utf-8') as f:
        json.dump(fe, f, indent=2)
    print(f"Frontend parsed: {len(fe)} pages dumped to backend/scripts/frontend_inspection.json")

    be = inspect_backend_routers()
    with open('backend/scripts/backend_inspection.json', 'w', encoding='utf-8') as f:
        json.dump(be, f, indent=2)
    print(f"Backend parsed: {len(be)} routers dumped to backend/scripts/backend_inspection.json")
