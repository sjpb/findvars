#!/usr/bin/env python
import yaml # package pyyaml
import sys, re, pprint, os

NON_ANSIBLE_MAGIC_VARS = 'group_names groups hostvars inventory_hostname inventory_hostname_short inventory_dir inventory_file omit play_hosts playbook_dir role_name role_names role_path item'.split()
OPERATORS = '< <= = == != >= > ! / * // % ^ |'.split()
KEYWORDS = 'is defined or and not changed bool mandatory None'.split()
FILTERS = 'round tojson attrforceescape map safe trim batch format max select truncate capitalize groupby min selectattr unique center indent pprint slice upper default int random sort urlencode dictsort join reject string urlize escape last rejectattr striptags wordcount filesizeformat length replace sum wordwrap first list reverse title xmlattr'.split()
def parse_expr(expr):
    # really hacky!
    parts = re.split(r'\s+|\w+\(|\)|\(|\)|,', expr)
    return parts

def is_var(s):
    # actually "non-magic" vars
    if s == '':
        return False
    if s.startswith('ansible_'): # NB this isn't strictly true but...
        return False
    if s in NON_ANSIBLE_MAGIC_VARS:
        return False
    if s in OPERATORS:
        return False
    if s in KEYWORDS:
        return False
    if s.startswith(('"', "'")): # is constant
        return False
    if s in FILTERS:
        return False
    return True

def walk(node, in_when=False, collected=None):
    if collected is None:
        collected = []
    if isinstance(node, list):
        for item in node:
            walk(item, False, collected)
    elif isinstance(node, dict):
        if 'when' in node:
            walk(node['when'], True, collected)
        for item in node.values(): # TODO: need to handle non-{{}} values in e.g. loop
            walk(item, in_when, collected)
    elif isinstance(node, str):
        if in_when:
            matches = [node]
        else:
            matches = re.findall(r'{{\s?([^{}]+)\s?}}', node)
        if matches:
            #print(node)
            exprs = [e.strip() for e in matches]
            #print(exprs)
            for expr in exprs:
                vars = [p for p in parse_expr(expr) if is_var(p)]
                collected.extend(vars)
                # for v in vars:
                #     print(' ', v)
                #print(' ', ' : '.join(vars))
    return collected

def read(path):
    print('%s:' % path)
    with open(path) as f:
        data = yaml.load(f.read(), Loader=yaml.Loader)
    vars = sorted(set(walk(data)))
    if vars:
        for v in vars:
            print('  -', v)

if __name__ == '__main__':
    path = sys.argv[1]
    if os.path.isdir(path):
        for dirpath, dirnames, filenames in os.walk(path):
            for fn in filenames:
                if os.path.splitext(fn)[1] != '.yml':
                    continue
                read(os.path.join(dirpath, fn))
            
    else:
        read(path)
        