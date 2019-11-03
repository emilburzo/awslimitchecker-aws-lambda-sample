#!/usr/bin/env python
"""
awslimitchecker/docs/examples/check_aws_limits.py

awslimitchecker example Python wrapper - see README.rst for information

The latest version of this package is available at:
<https://github.com/jantman/awslimitchecker>

################################################################################

Copyright 2015-2018 Jason Antman <jason@jasonantman.com>

    This file is part of awslimitchecker, also known as awslimitchecker.

    awslimitchecker is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    awslimitchecker is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with awslimitchecker.  If not, see <http://www.gnu.org/licenses/>.

The Copyright and Authors attributions contained herein may not be removed or
otherwise altered, except to add the Author attribution of a contributor to
this work. (Additional Terms pursuant to Section 7b of the AGPL v3)

################################################################################

While not legally required, I sincerely request that anyone who finds
bugs please submit them at <https://github.com/jantman/awslimitchecker> or
to me via email, and that you send any contributions or improvements
either as a pull request on GitHub, or to me via email.

################################################################################

AUTHORS:
Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>

################################################################################
"""

import logging

from awslimitchecker.checker import AwsLimitChecker

# BEGIN configuration for thresholds and limit overrides
from util import send_mail

AWS_LIMIT_OVERRIDES = {
    #    'EC2': {
    #        'Running On-Demand EC2 instances': 400,
    #     },
}

AWS_THRESHOLD_OVERRIDES = {
    # 'Lambda': {
    #     'Total Code Size (MiB)': {'warning': {'percent': 85}},
    # },
}
# END configuration for thresholds and limit overrides

EMAIL_SUBJECT_WARNING = "awslimitchecker - warning"
EMAIL_SUBJECT_CRITICAL = "awslimitchecker - critical"

EMAIL_TO_WARNING = "warning@example.com"
EMAIL_TO_CRITICAL = "critical@example.com"

logger = logging.getLogger(__name__)


class CheckAWSLimits(object):
    """check AWS usage against service limits"""

    def check_limits(self, verbose=False):
        """
        Run the actual usage and limit check, with overrides.

        see: http://awslimitchecker.readthedocs.org/en/latest/python_usage.html#ci-deployment-checks
        """
        # instantiate the class
        checker = AwsLimitChecker()
        # set your overrides
        checker.set_threshold_overrides(AWS_THRESHOLD_OVERRIDES)
        checker.set_limit_overrides(AWS_LIMIT_OVERRIDES)

        print("Checking AWS resource usage; WARNING threshold {w}% of "
              "limit, CRITICAL threshold {c}% of limit".format(
            w=checker.warning_threshold,
            c=checker.critical_threshold))

        # check usage against thresholds
        # if we didn't support verbose output, we could just iterate the return
        # value of this to be a bit more efficient.
        checker.check_thresholds()

        # save state for exit code and summary
        warnings = []
        criticals = []

        # iterate the results
        for service, svc_limits in sorted(checker.get_limits().items()):
            for limit_name, limit in sorted(svc_limits.items()):
                have_alarms = False
                # check warnings and criticals for each Limit
                for warn in limit.get_warnings():
                    warnings.append("{service} '{limit_name}' usage "
                                    "({u}) exceeds warning threshold "
                                    "(limit={l})".format(
                        service=service,
                        limit_name=limit_name,
                        u=str(warn),
                        l=limit.get_limit(),
                    ))
                    have_alarms = True
                for crit in limit.get_criticals():
                    criticals.append("{service} '{limit_name}' usage "
                                     "({u}) exceeds critical threshold"
                                     " (limit={l})".format(
                        service=service,
                        limit_name=limit_name,
                        u=str(crit),
                        l=limit.get_limit(),
                    ))
                    have_alarms = True
                if not have_alarms and verbose:
                    print("{service} '{limit_name}' OK: {u} (limit={l})".format(
                        service=service,
                        limit_name=limit_name,
                        u=limit.get_current_usage_str(),
                        l=limit.get_limit()
                    ))
        if verbose:
            print("\n\n")
        return (warnings, criticals)

    def run(self, verbose=False):
        """
        Main entry point.
        """
        warnings, criticals = self.check_limits(verbose=verbose)
        # output
        if len(warnings) > 0:
            print("\nWARNING:\n")
            for w in warnings:
                print(w)
        if len(criticals) > 0:
            print("\nCRITICAL:\n")
            for c in criticals:
                print(c)

        # alerts
        if len(warnings) > 0:
            body = '\n'.join(warnings)
            send_mail(EMAIL_SUBJECT_WARNING, body, [EMAIL_TO_WARNING])

        if len(criticals) > 0:
            body = '\n'.join(criticals)
            send_mail(EMAIL_SUBJECT_CRITICAL, body, [EMAIL_TO_CRITICAL])

        # summary
        if len(warnings) > 0 or len(criticals) > 0:
            print("\n{c} limit(s) above CRITICAL threshold; {w} limit(s) above "
                  "WARNING threshold".format(c=len(criticals), w=len(warnings)))
        else:
            print("All limits are within thresholds.")


def handler(event, _):
    # print("new lambda run, event:" + str(event))
    checker = CheckAWSLimits()
    checker.run(verbose=True)


if __name__ == "__main__":
    print("new CLI run")
    handler(None, None)
