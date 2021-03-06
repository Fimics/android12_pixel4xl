#
# Copyright 2008 Google Inc. All Rights Reserved.
#
"""Command line interface for autotest

This module contains the generic CLI processing

See topic_common.py for a High Level Design and Algorithm.

This file figures out the topic and action from the 2 first arguments
on the command line and imports the <topic> module.

It then creates a <topic>_<action> object, and calls it parses),
execute() and output() methods.
"""

from __future__ import print_function

__author__ = 'jmeurin@google.com (Jean-Marc Eurin)'

import os, sys, re, traceback

import common
from autotest_lib.cli import topic_common
from autotest_lib.client.common_lib import lsbrelease_utils
from autotest_lib.server import utils


def main():
    """
    The generic syntax is:
    atest <topic> <action> <options>
    atest-<topic> <action> <options>
    atest --help
    """
    _disallow_root_user_on_moblab()
    cli = os.path.basename(sys.argv[0])
    syntax_obj = topic_common.atest()

    # Normalize the various --help, -h and help to -h
    sys.argv = [re.sub('--help|help', '-h', arg) for arg in sys.argv]

    match = re.search('^atest-(\w+)$', cli)
    if match:
        topic = match.group(1)
    else:
        if len(sys.argv) > 1:
            topic = sys.argv.pop(1)
        else:
            syntax_obj.invalid_syntax('No topic argument')


    if topic == '-h':
        sys.argv.insert(1, '-h')
        syntax_obj.parse()

    # Import the topic specific file
    cli_dir = os.path.abspath(os.path.dirname(__file__))
    if not os.path.exists(os.path.join(cli_dir, '%s.py' % topic)):
        syntax_obj.invalid_syntax('Invalid topic %s' % topic)
    topic_module = common.setup_modules.import_module(topic,
                                                      'autotest_lib.cli')

    # If we have a syntax error now, it should
    # refer to the topic class.
    topic_class = getattr(topic_module, topic)
    topic_obj = topic_class()

    if len(sys.argv) > 1:
        action = sys.argv.pop(1)

        if action == '-h':
            action = 'help'
            sys.argv.insert(1, '-h')
    else:
        topic_obj.invalid_syntax('No action argument')

    # Any backward compatibility changes?
    action = topic_obj.backward_compatibility(action, sys.argv)

    # Instantiate a topic object
    try:
        action_class = getattr(topic_module, topic + '_' + action)
    except AttributeError:
        topic_obj.invalid_syntax('Invalid action %s' % action)

    action_obj = action_class()

    action_obj.parse()
    try:
        try:
            results = action_obj.execute()
        except topic_common.CliError:
            pass
        except Exception as err:
            traceback.print_exc()
            action_obj.generic_error("Unexpected exception: %s" % err)
        else:
            try:
                action_obj.output(results)
            except Exception:
                traceback.print_exc()
    finally:
        return action_obj.show_all_failures()


def _disallow_root_user_on_moblab():
    """Running these tools as root interferes with moblab services"""
    if lsbrelease_utils.is_moblab():
        utils.verify_not_root_user()
