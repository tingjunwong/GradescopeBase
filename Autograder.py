"""
/*
 * @Author: ThaumicMekanism [Stephan K.] 
 * @Date: 2020-01-23 20:57:36 
 * @Last Modified by: ThaumicMekanism [Stephan K.]
 * @Last Modified time: 2020-01-30 16:26:37
 */
"""
"""
This is the base of the autograder.
"""
import json
import time
import datetime
import os
from .AutograderTest import AutograderTest, global_tests, Max
from .AutograderErrors import AutograderSafeEnvError
from .AutograderSetup import global_setups
from .AutograderTeardown import global_teardowns
from .Utils import root_dir, submission_dir, results_path, get_welcome_message

submission_metadata = "/autograder/submission_metadata.json"

printed_welcome_message = False

class RateLimit:
    def __init__(
        self,
        tokens:int=None,
        seconds:int=0,
        minutes:int=0,
        hours:int=0,
        days:int=0,
        reset_time:str=None
    ):
        self.tokens = tokens
        self.seconds = seconds
        self.minutes = minutes
        self.hours = hours
        self.days = days
        self.reset_time = reset_time

class Autograder:
    def __init__(self, rate_limit=None, reverse_tests=False, export_tests_after_test=True):
        self.tests = []
        self.setups = []
        self.teardowns = []
        self.results_file = results_path()
        self.score = None
        self.output = None
        self.visibility = None
        self.stdout_visibility = None
        self.extra_data = {}
        self.leaderboard = None
        self.reverse_tests = reverse_tests
        self.export_tests_after_test = export_tests_after_test
        # rate_limit takes in a RateLimit class.
        # reset_time is when you want to reset the submission time. You
        # can leave it out to ignore. Put the time stirng in this format:
        #  "2018-11-29T16:15:00"
        self.rate_limit:RateLimit = rate_limit
        self.start_time = datetime.datetime.now()

    @staticmethod
    def run(ag = None):
        global printed_welcome_message
        if not printed_welcome_message:
            printed_welcome_message = True
            print(get_welcome_message())
        def f(ag):
            for t in global_tests:
                ag.add_test(t)
            for s in global_setups:
                ag.add_setup(s)
            for t in global_teardowns:
                ag.add_teardown(t)
            ag.execute()
        Autograder.main(f, ag=ag)

    @staticmethod
    def main(f, ag=None):
        global printed_welcome_message
        if not printed_welcome_message:
            printed_welcome_message = True
            print(get_welcome_message())
        if ag is None:
            ag = Autograder()
        def handler():
            ag.ag_fail("An exception occured in the autograder's main function. Please contact a TA to resolve this issue.")
            return True
        def wrapper():
            f(ag)
        ag.safe_env(wrapper, handler)

    def dump_results(self, data: dict) -> None:
        jsondata = json.dumps(data, ensure_ascii=False)
        with open(self.results_file, "w") as f:
            f.write(jsondata)

    def add_test(self, test):
        if isinstance(test, AutograderTest):
            self.tests.append(test)
            return
        raise ValueError("You must add type Test to the autograder.")

    def add_setup(self, setupfn):
        self.setups.append(setupfn)

    def add_teardown(self, teardownfn):
        self.teardowns.append(teardownfn)

    def set_score(self, score):
        self.score = score
    
    def add_score(self, addition):
        if self.score is None:
            self.score = 0
        self.score += addition
    
    def get_score(self):
        return self.score

    def print(self, *args, sep=' ', end='\n', file=None, flush=True):
        if self.output is None:
            self.output = ""
        self.output += sep.join(args) + end

    def create_test(self, *args, **kwargs):
        test = AutograderTest(*args, **kwargs)
        self.add_test(test)

    def ag_fail(self, message: str, extra: dict={}, exit_prog=True) -> None:
        data = {
            "score": 0,
            "output": message
        }
        data.update(extra)
        self.dump_results(data)
        if exit_prog:
            import sys
            sys.exit()
    
    def safe_env(self, f, handler=None):
        try:
            return f()
        except Exception as exc:
            print("An exception occured in the safe environment!")
            import traceback
            traceback.print_exc()
            print(exc)
            if handler is not None:
                try:
                    h = handler()
                    if h:
                        return AutograderSafeEnvError(h)
                except Exception as exc:
                    print("An exception occured while executing the exception handler!")
                    traceback.print_exc()
            self.ag_fail("An unexpected exception ocurred while trying to execute the autograder. Please try again or contact a TA if this persists.")
            return AutograderSafeEnvError(exc)

    def run_tests(self):
        global printed_welcome_message
        if not printed_welcome_message:
            printed_welcome_message = True
            print(get_welcome_message())
        def handle_failed():
                self.set_score(0)
                if "sub_counts" in self.extra_data:
                    self.print("Since the autograder failed to run, you will not use up a token!")
                    self.extra_data["sub_counts"] = 0
        for setup in self.setups:
            if not setup.run(self):
                self.print("An error occurred in the setup of the Autograder!")
                handle_failed()
                return False
        for test in self.tests:
            test.run(self)
            if self.export_tests_after_test:
                self.generate_results()
        for teardown in self.teardowns:
            if not teardown.run(self):
                self.print("An error occurred in the teardown of the Autograder!")
                handle_failed()
                return False
        return True

    def generate_results(self, test_results=None, dump=True):
        results = {
            "execution_time": (datetime.datetime.now() - self.start_time).total_seconds(),
        }
        if test_results is None:
            tests = []
            if self.reverse_tests:
                tsts = reversed(self.tests)
            else:
                tsts = self.tests
            for test in tsts:
                res = test.get_results()
                if res:
                    tests.append(res)
            if tests:
                results["tests"] = tests
        else:
            if isinstance(test_results, list):
                results["tests"] = test_results
        if self.score is not None:
            results["score"] = self.score
        else:
            if "tests" not in results or len(results["tests"]) == 0 or not any(["score" in t for t in results["tests"]]):
                results["score"] = 0
                self.print("This autograder does not set the main score or have any tests which give points!")
        if self.output is not None:
            results["output"] = self.output
        if self.visibility is not None:
            results["visibility"] = self.visibility
        if self.stdout_visibility is not None:
            results["stdout_visibility"] = self.stdout_visibility
        if self.extra_data:
            results["extra_data"] = self.extra_data
        if self.leaderboard is not None:
            results["leaderboard"] = self.leaderboard
        if dump:
            self.dump_results(results)
        return results
        
    def execute(self):
        global printed_welcome_message
        if not printed_welcome_message:
            printed_welcome_message = True
            print(get_welcome_message())
        self.rate_limit_main()
        if not self.run_tests():
            print("An error has occured when attempting to run all tests.")
        self.generate_results()

    @staticmethod
    def root_dir() -> str:
        return root_dir()

    @staticmethod
    def submission_dir() -> str:
        return submission_dir()
    
    def rate_limit_main(self):
        if isinstance(self.rate_limit, RateLimit) and self.rate_limit.tokens is not None:
                    tokens = self.rate_limit.tokens
                    restart_subm_string = self.rate_limit.reset_time
                    s = self.rate_limit.seconds
                    m = self.rate_limit.minutes
                    h = self.rate_limit.hours
                    d = self.rate_limit.days
                    regen_time_seconds = s + 60 * (m + 60 * (h + (24 * d)))
                    def get_submission_time(s):
                        return s[:-13]
                    def pretty_time_str(s, m, h, d):
                        sstr = "" if s == 0 else str(s) + " second"
                        sstr += "" if sstr == "" or s == 1 else "s"
                        mstr = "" if m == 0 else str(m) + " minute"
                        mstr += "" if mstr == "" or m == 1 else "s"
                        hstr = "" if h == 0 else str(h) + " hour"
                        hstr += "" if hstr == "" or h == 1 else "s"
                        dstr = "" if d == 0 else str(d) + " day"
                        dstr += "" if dstr == "" or d == 1 else "s"
                        st = dstr
                        for tmpstr in [hstr, mstr, sstr]:
                            if st != "" and tmpstr != "":
                                st += " "
                            st += tmpstr
                        if st == "":
                            st = "none"
                        return st
                    with open(submission_metadata, "r") as jsonMetadata:
                        metadata = json.load(jsonMetadata)
                    current_subm_string = get_submission_time(metadata["created_at"])
                    current_time = time.strptime(current_subm_string,"%Y-%m-%dT%H:%M:%S")
                    restart_time = time.strptime(restart_subm_string, "%Y-%m-%dT%H:%M:%S") if restart_subm_string is not None else None
                    tokens_used = 0
                    print("=" * 30)
                    for i, v in enumerate(metadata["previous_submissions"]):
                        subm_string = get_submission_time(v["submission_time"])
                        subm_time = time.strptime(subm_string,"%Y-%m-%dT%H:%M:%S")
                        if restart_time is not None and time.mktime(subm_time) - time.mktime(restart_time) < 0:
                            print("Ignoring a submission, too early!")
                            continue
                        print("Current time: " + str(time.mktime(current_time)))
                        print("Subm time: " + str(time.mktime(subm_time)))
                        if (time.mktime(current_time) - time.mktime(subm_time) < regen_time_seconds): 
                            try:
                                print(metadata["previous_submissions"][i])
                                print("Tokens used: " + str(tokens_used))
                                print(str(metadata["previous_submissions"][i].keys()))
                                print("Current submission data: " + str(metadata["previous_submissions"][i]["results"]["extra_data"]))
                                if (metadata["previous_submissions"][i]["results"]["extra_data"]["sub_counts"] == 1): 
                                    tokens_used = tokens_used + 1
                            except: 
                                tokens_used = tokens_used + 1
                                pass
                        print("-" * 30)
                    print("=" * 30)
                    if tokens_used < tokens:
                        self.extra_data["sub_counts"] = 1
                        tokens_used += 1 # This is to include the current submission.
                        self.print(f"Students can get up to {tokens} graded submissions within any given period of {pretty_time_str(s, m, h, d)}. In the last period, you have had {tokens_used} graded submissions.")
                    else:
                        self.extra_data["sub_counts"] = 0
                        self.print(f"Students can get up to {tokens} graded submissions within any given period of {pretty_time_str(s, m, h, d)}. You have already had {tokens_used} graded submissions within the last {pretty_time_str(s, m, h, d)}, so the results of your last graded submission are being displayed. This submission will not count as a graded submission.")
                        
                        prev_subs = metadata["previous_submissions"]
                        prev_sub = prev_subs[len(prev_subs) - 1]
                        if "results" not in prev_sub or "tests" not in prev_sub["results"]:
                            self.print("[ERROR]: Could not pull the data from your previous submission! This is probably due to it not have finished running!")
                            tests = []
                            self.set_score(0)
                        else:
                            res = prev_sub["results"]
                            tests = res["tests"]
                            self.set_score(prev_sub.get("score"))
                        self.generate_results(test_results=tests)
                        import sys
                        sys.exit()

    def rate_limit_unset_submission(self):
        self.extra_data["sub_counts"] = 0

    @staticmethod
    def FAIL(msg):
        ag = Autograder()
        ag.print(msg)
        ag.set_score(0)
        ag.generate_results()