"""Classify only documented malformed-seed subprocess refusals."""
def is_seed_refusal(result):
    if result.returncode == -11:
        return True
    if result.returncode != 1:
        return False
    lines = result.stderr.splitlines()
    if not lines or 'seed must be an integer' in result.stderr:
        return False
    if any(line.split(':')[0] in ('TypeError', 'RecursionError') for line in lines):
        return True
    return (lines[-1].startswith('ValueError: ')
            and 'cannot be used to seed a numpy.random.RandomState instance' in lines[-1]
            and any('in check_random_state' in line for line in lines))
