import json, os

from constants import (
    FAIL_TO_PASS,
    FAIL_TO_FAIL,
    PASS_TO_PASS,
    PASS_TO_FAIL,
    TestStatus,
)
from getters import (
    get_file_name_from_lp,
    get_repo_from_lp,
    log_path_to_sms,
    test_failed,
    test_passed,
)
from log_parsers import MAP_REPO_TO_PARSER


def convert_log_to_ground_truth(
    log_fp: list, save_dir: str = None, verbose: bool = False
) -> dict:
    """
    Convert log file generated from check instances into ground truth dict

    Args:
        log_dir (str): path to log files
        save_dir (str): path to save results
        verbose (bool): whether or not to show logs
    Returns:
        dict: test case to test status mapping
    """
    if verbose:
        print(f"[DEBUG] Received log_fp: {log_fp}")
        print(f"[DEBUG] Save directory: {save_dir if save_dir else 'None'}")

    inst_file_name = get_file_name_from_lp(log_fp)
    if verbose:
        print(f"[DEBUG] Extracted instance file name: {inst_file_name}")

    repo = get_repo_from_lp(log_fp)
    if verbose:
        print(f"[DEBUG] Extracted repository from log_fp: {repo}")

    log_parser = MAP_REPO_TO_PARSER[repo]
    if verbose:
        print(f"[DEBUG] Using log parser for repo '{repo}': {log_parser}")

    sms, found = log_path_to_sms(log_fp, log_parser)
    if verbose:
        print(f"[DEBUG] Log parsing result: found = {found}")
        print(f"[DEBUG] Parsed SMS (before/after): {sms}")

    if not found:
        raise ValueError(
            "Log file could not be parsed properly (Before, After Logs not found)"
        )

    sm_before, sm_after = sms[0], sms[1]
    if verbose:
        print(f"[DEBUG] Test status before change: {sm_before}")
        print(f"[DEBUG] Test status after change: {sm_after}")

    status_ground_truth = {
        FAIL_TO_PASS: [],
        FAIL_TO_FAIL: [],
        PASS_TO_PASS: [],
        PASS_TO_FAIL: [],
    }

    if verbose:
        print(f"[DEBUG] Initialized status_ground_truth dictionary: {status_ground_truth}")

    for test, status in sm_after.items():
        if verbose:
            print(f"[DEBUG] Processing test '{test}' with status '{status}'")

        if status == TestStatus.PASSED.value:
            if test_passed(test, sm_before):
                status_ground_truth[PASS_TO_PASS].append(test)
                if verbose:
                    print(f"[DEBUG] Test '{test}' moved from PASS to PASS")
            elif test_failed(test, sm_before):
                status_ground_truth[FAIL_TO_PASS].append(test)
                if verbose:
                    print(f"[DEBUG] Test '{test}' moved from FAIL to PASS")
        if status == TestStatus.FAILED.value:
            if test_passed(test, sm_before):
                status_ground_truth[PASS_TO_FAIL].append(test)
                if verbose:
                    print(f"[DEBUG] Test '{test}' moved from PASS to FAIL")
            elif test_failed(test, sm_before):
                status_ground_truth[FAIL_TO_FAIL].append(test)
                if verbose:
                    print(f"[DEBUG] Test '{test}' moved from FAIL to FAIL")

    if verbose:
        print(f"[DEBUG] Final status_ground_truth dictionary: {status_ground_truth}")

    if save_dir is not None:
        results_file = f"{inst_file_name.split('.')[0]}.json"
        if verbose:
            print(f"[DEBUG] Preparing to save results to {os.path.join(save_dir, results_file)}")
        with open(os.path.join(save_dir, results_file), "w") as f:
            json.dump(status_ground_truth, f, indent=4)
            if verbose:
                print(f"[DEBUG] Results successfully saved to {os.path.join(save_dir, results_file)}")

    return status_ground_truth

