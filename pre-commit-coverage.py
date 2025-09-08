import glob
import os
import re
import subprocess

import yaml


def get_python_files():
    """Get all Python files recursively in the project."""
    python_files = glob.glob('./**/*.py', recursive=True)
    return python_files


def is_excluded(file_path, exclude_pattern):
    """Check if a file matches the exclude pattern."""
    if exclude_pattern != None:
        return bool(re.search(exclude_pattern, str(file_path)))
    return False


def is_included(file_path, include_pattern):
    """Check if a file matches the include(file) pattern."""
    if include_pattern != None:
        clean_path = os.path.normpath(file_path).replace('\\', '/')
        if clean_path.startswith('./'):
            clean_path = clean_path[2:]

        return bool(re.search(include_pattern, clean_path))

    return True

# unused
def output_text_table(data):
    # Get all unique hooks
    all_hooks = set()
    for file_data in data.values():
        all_hooks.update(file_data.keys())
    all_hooks = sorted(all_hooks)

    # Calculate column widths
    file_width = max(len(str(fp)) for fp in data.keys()) + 2
    hook_width = 8  # Width for hook results

    # Print header
    header = "File".ljust(file_width)
    for hook in all_hooks:
        header += hook.ljust(hook_width)
    print(header)
    print("-" * len(header))

    # Print rows
    for file_path, hooks_data in data.items():
        row = file_path.ljust(file_width)
        for hook in all_hooks:
            value = str(hooks_data.get(hook, 'N/A'))
            row += value.ljust(hook_width)
        print(row)


def display_comprehensive_report(data):
    """
    Display both the grid table and statistics in one comprehensive output
    """
    # First, display the grid table
    print("=" * 80)
    print("PRE-COMMIT HOOK RESULTS - DETAILED GRID")
    print("=" * 80)

    # Get all unique hooks
    all_hooks = set()
    for file_data in data.values():
        all_hooks.update(file_data.keys())
    all_hooks = sorted(all_hooks)

    # Calculate column widths
    file_width = max(len(str(fp)) for fp in data.keys()) + 2
    hook_width = 8  # Width for hook results

    # Print header
    header = "File".ljust(file_width)
    for hook in all_hooks:
        header += hook.ljust(hook_width)
    print(header)
    print("-" * len(header))

    # Print rows
    for file_path, hooks_data in data.items():
        row = file_path.ljust(file_width)
        for hook in all_hooks:
            value = str(hooks_data.get(hook, 'N/A'))
            row += value.ljust(hook_width)
        print(row)

    print("\n" + "=" * 80)
    print("PRE-COMMIT HOOK RESULTS - STATISTICS SUMMARY")
    print("=" * 80)

    # Now calculate and display statistics
    total_valid = 0
    total_s = 0
    total_f = 0

    # Calculate overall statistics
    for file_data in data.values():
        for result in file_data.values():
            if result is not None:
                total_valid += 1
                if result == 'S':
                    total_s += 1
                elif result == 'F':
                    total_f += 1

    overall_success = (total_s / total_valid * 100) if total_valid > 0 else 0
    overall_failure = (total_f / total_valid * 100) if total_valid > 0 else 0

    # Calculate per-hook statistics
    hook_percentages = {}
    for hook in all_hooks:
        hook_valid = 0
        hook_s = 0
        hook_f = 0

        for file_data in data.values():
            result = file_data.get(hook)
            if result is not None:
                hook_valid += 1
                if result == 'S':
                    hook_s += 1
                elif result == 'F':
                    hook_f += 1

        if hook_valid > 0:
            hook_percentages[hook] = {
                'valid_checks': hook_valid,
                'success_count': hook_s,
                'failure_count': hook_f,
                'success_percentage': (hook_s / hook_valid * 100),
                'failure_percentage': (hook_f / hook_valid * 100)
            }

    # Display overall statistics
    print(f"\nOVERALL STATISTICS:")
    print(f"Total files processed: {len(data)}")
    print(f"Total valid hook checks: {total_valid}")
    print(f"Successes: {total_s} ({overall_success:.1f}%)")
    print(f"Failures: {total_f} ({overall_failure:.1f}%)")

    # Display per-hook statistics in a table format
    print(f"\nPER-HOOK STATISTICS:")
    print("-" * 60)
    print(f"{'Hook':<20} {'Checks':<8} {'Success':<8} {'Failure':<8} {'Success %':<10} {'Failure %':<10}")
    print("-" * 60)

    for hook in sorted(hook_percentages.keys()):
        stats = hook_percentages[hook]
        print(f"{hook:<20} {stats['valid_checks']:<8} {stats['success_count']:<8} {stats['failure_count']:<8} "
              f"{stats['success_percentage']:<10.1f} {stats['failure_percentage']:<10.1f}")

    print("-" * 60)


def run_hook(file_path, hook_id, hook_args):
    cmd = ["pre-commit", "run", hook_id, "--files", file_path]
    if hook_args and isinstance(hook_args, list) and hook_args:
        args_string = " ".join(hook_args)
        cmd.append(f"--args={args_string}")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False
    )
    return "S" if result.returncode == 0 else "F"


def main():
    with open(".pre-commit-config.yaml", "r") as f:
        config = yaml.safe_load(f)

    hooks_info = {}
    result = {}

    for repo in config["repos"]:
        for hook in repo.get("hooks", []):
            hook_id = hook["id"]
            hooks_info[hook_id] = {
                "exclude": hook.get("exclude"),
                "include": hook.get("files"),
                "args": hook.get("args")
            }
    python_files = get_python_files()
    print(len(python_files))

    for py_file in python_files:
        result[py_file] = {}
        for hook in hooks_info:
            include_pattern = hooks_info[hook]["include"]
            exclude_pattern = hooks_info[hook]["exclude"]
            hook_args = hooks_info[hook]["args"]
            if is_included(py_file, include_pattern) and not is_excluded(py_file, exclude_pattern):
                result[py_file][hook] = run_hook(py_file, hook, hook_args)
            else:
                result[py_file][hook] = None
    display_comprehensive_report(result)


if __name__ == "__main__":
    main()
