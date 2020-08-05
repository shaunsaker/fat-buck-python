import sys
import subprocess
import argparse
from dateutil.relativedelta import relativedelta
import utils

# parse args
argParser = argparse.ArgumentParser()
argParser.add_argument("--startDate", type=str)
argParser.add_argument("--endDate", type=str)
argParser.add_argument("--fromIndex", type=int)
argParser.add_argument("--toIndex", type=int)
args = argParser.parse_known_args()

startDateArg = args[0].startDate
startDate = utils.dateStringToDate(startDateArg)
endDateArg = args[0].endDate
finalDate = utils.dateStringToDate(endDateArg)
fromIndex = args[0].fromIndex
toIndex = args[0].toIndex


# between the start and end date
# every month, call simulate with new params
while startDate <= finalDate:
    startDateString = utils.dateToDateString(startDate)
    endDate = utils.getEndOfMonth(startDate + relativedelta(months=1))
    endDateString = utils.dateToDateString(endDate)
    print(f"Running simulate as subprocess for {startDateString} to {endDateString}")
    subprocess.call(
        [
            sys.executable,
            "simulate.py",
            "--startDate",
            startDateString,
            "--endDate",
            endDateString,
        ]
    )

    startDate = endDate
