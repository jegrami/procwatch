import sys
import time

print("flaky_worker: starting up ....")
time.sleep(2)

outcome = sys.argv[1] if len(sys.argv) > 1 else "Success!"

if outcome == "fail": 
    print("flaky_worker: something went wrong. exiting with code 1")
    sys.exit(1)
else:
    print("flaky_worker: work complete, exiting with 0")
    sys.exit(0)




