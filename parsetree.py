HIDE_TYPES = True

CLEAN_PATTERN = r'(?:C3NSTR|S2E)(.+)'

SUBSTITUTIONS = [
    ('intinf', 'int'),
    ('eqeq', '=='),
    ('mul_.+', '*'),
    ('add_.+', '+'),
    ('sub_.+', '-'),
    ('prop', '')
    ]

TYPES = ['int', 'var']

class Node():
    def __init__(self):
        self.children = []
        self.name = '?'

    def __str__(self):
        if self.name == '':
            return ', '.join(map(str, self.children))

        elif _symbolic(self.name) and len(self.children) == 2:
            left, right = self.children
            return '(' + str(left) + ' ' + self.name + ' ' + str(right) + ')'

        elif len(self.children) == 0:
            return self.name

        elif len(self.children) == 1:
            if HIDE_TYPES:
                return ', '.join(map(str, self.children))
            else:
                return self.name + '(' + ', '.join(map(str, self.children)) + ')'
        else:
            return self.name + '(' + ', '.join(map(str, self.children)) + ')'


def _parse(formula):
    tokens = _tokenize(formula)

    stack, root = [], Node()
    stack.append(root)
    current = root

    for t in tokens:
        if t == '(':
            node = Node()
            stack.append(current)

            current.children.append(node)
            current = node

        elif t == ')':
            current = stack.pop()

        elif t in [',', ';']:
            node = Node()

            parent = stack[-1]
            parent.children.append(node)

            current = node

        else:
            current.name = t

    return root


def _tokenize(s):
    tokens = []
    name = ''
    for ch in s:
        if ch == ' ':
            if name:
                tokens.append(name)
                name = ''
            continue
        elif ch in ['(', ')', ',', ';']:
            if name:
                tokens.append(name)
                name = ''
            tokens.append(ch)
        else: # start of a name or value
            name += ch

    if name:
        tokens.append(name)

    return tokens


def _rename(node):
    from re import search, sub

    matches = search(CLEAN_PATTERN, node.name)
    if matches:
        node.name = matches.group(1)

    for pat, repl in SUBSTITUTIONS:
        if search(pat, node.name):
            node.name = sub(pat, repl, node.name)

    if len(node.children) > 0:
        node.children = [_rename(child) for child in node.children]

    return node


def _simplify(node):
    if len(node.children) > 0:
        new_children = []
        for child in node.children:
            if child.name != 'main':
                new_children.append(_simplify(child))

        node.children = new_children

    if node.name == 'app':
        new_node = Node()
        new_node.name = node.children[0].children[0].name
        new_node.children = node.children[1:]
        node = new_node

    if node.name == 'var':
        child = node.children[0]

        if '$' in child.name:
            child.name = child.name[:child.name.index('$')]

        child.children = []

    return node


def _symbolic(name):
    return all(map(lambda ch: ch in '!@#$%^&*=><+-', name))


def _print_tree(node, pre=''):
    print(pre + node.name)
    for child in node.children:
        _print_tree(child, pre + '\t')


def prettify(formula):
    """Takes a string from the ATS constraint solver representing an unsolved
    constraint, and returns a better string representation of it.
    """
    return str(_simplify(_rename(_parse(formula))))
