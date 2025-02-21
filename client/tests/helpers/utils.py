import os
import time

# Create a logs directory
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)


def wait_for_condition(condition_func, timeout=5, interval=0.1):
    """
    Wait for a condition to be met.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        if condition_func():
            return True
        time.sleep(interval)
    return False


def write_to_log(test_name, protocol_type, bytes_received, bytes_sent, time_elapsed):
    log_file = os.path.join(
        LOG_DIR, f"integration_metrics_{protocol_type}.log")

    # Read existing log entries
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            lines = f.readlines()
    else:
        lines = []

    # Remove existing test entry
    new_lines = []
    in_test_block = False
    for line in lines:
        if line.startswith("[TEST METRICS]"):
            in_test_block = test_name in line  # Start removing if it's the same test name
        if not in_test_block:
            new_lines.append(line)
        if in_test_block and line.strip() == "":  # Stop removing when an empty line is encountered
            in_test_block = False

    # Append the new test entry
    log_message = (
        f"[TEST METRICS] {test_name}\n"
        f"Time taken: {time_elapsed:.3f} seconds\n"
        f"Total bytes sent: {bytes_sent}\n"
        f"Total bytes received: {bytes_received}\n\n"
    )
    new_lines.append(log_message)

    # Write back the modified content
    with open(log_file, "w") as f:
        f.writelines(new_lines)
