#!/usr/bin/env python3

from __future__ import print_function
import os, sys


def to_symbol(path):
    p, result = path, []
    while True:
        p, folder = os.path.split(p)
        if folder:
            result.append(folder)
        else:
            if p:
                result.append(p)
            break

    result.reverse()
    return result


def importables(root):
    for dirpath, dirnames, filenames in os.walk(root):
        has_init = '__init__.py' in filenames
        is_root = dirpath == root

        # if has_init and is_root:
        #     print(INIT_ROOT_WARNING.format(**locals()), file=sys.stder1r)

        if not (has_init or is_root):
            # The tree ends here
            dirnames.clear()
            continue

        dirnames[:] = [d for d in dirnames if not d.startswith('.')]
        path = os.path.relpath(dirpath, root)
        if not is_root:
            yield to_symbol(path)

        for f in filenames:
            if f.endswith('.py') and not f.startswith('_'):
                body = f[:-3]
                if body.isidentifier():
                    if is_root:
                        yield body
                    else:
                        yield to_symbol(os.path.join(path, body))


def canonical_roots(argv):
    roots = []

    for root in argv:
        r = os.path.abspath(os.path.normpath(os.path.expanduser(root)))
        if not os.path.exists(r):
            raise ValueError('Directory "%s" does not exist' % root)
        roots.append(r)

    return roots


def import_roots(argv):
    errors = []
    universe = {}

    roots = canonical_roots(argv)
    sys.path.extend(roots)

    for root in roots:
        for spacename in importables(root):
            try:
                namespace = __import__(spacename)
            except:
                errors.append((root, spacename))
            else:
                universe[spacename] = namespace
                for k, v in vars(namespace).items():
                    if not k.startswith('_'):
                        universe['%s.%s' % (spacename, k)] = v

    return universe, errors


def restrict(s, bound=79):
    return s if len(s) < bound else s[:bound - 3] + '...'


def print_universe(universe, bound=80):
    ns_length = max(len(k) for k in universe.keys())
    rbound = bound - ns_length - 3

    for address, value in sorted(universe.items()):
        line = '%s = %s' % (address, repr(value))
        print(restrict(line))


if __name__ == '__main__':
    argv = sys.argv[1:]

    def pop_arg(flag):
        try:
            return argv.remove(flag) or True
        except:
            return False

    use_all = pop_arg('-a')
    print_errors = pop_arg('-e')

    universe, errors = import_roots(argv)
    if use_all:
        modules = {k: v for k, v in sys.modules.items()
                   if not k.startswith('_')}
        universe = dict(modules, **universe)

    print_universe(universe)
    if print_errors:
        print('ERROR', *errors, file=sys.stderr, sep='\n')
