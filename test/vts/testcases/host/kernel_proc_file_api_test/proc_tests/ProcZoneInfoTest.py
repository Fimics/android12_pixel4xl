#
# Copyright (C) 2020 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from proc_tests import KernelProcFileTestBase
from proc_tests.KernelProcFileTestBase import repeat_rule, literal_token


class ProcZoneInfoTest(KernelProcFileTestBase.KernelProcFileTestBase):
    '''/proc/zoneinfo displays information about memory zones.'''

    t_APAGES = literal_token(r'pages\s')
    t_PAGESETS = literal_token(r'pagesets')
    t_CPU = literal_token(r'cpu')
    t_VM = literal_token(r'vm')
    t_STATS = literal_token(r'stats')
    t_THRESHOLD = literal_token(r'threshold')
    t_NODE = literal_token(r'Node')
    t_ZONE = literal_token(r'zone')
    t_PROTECTION = literal_token(r'protection')
    t_PERNODE = literal_token(r'per-node')
    t_LPAREN = literal_token(r'\(')
    t_RPAREN = literal_token(r'\)')

    t_ignore = ' '

    start = 'nodes'

    p_nodes = repeat_rule('node')
    p_lines = repeat_rule('line')
    p_cpus = repeat_rule('cpu')
    p_colonlines = repeat_rule('colonline')
    p_numcommas = repeat_rule('numcomma')

    def p_node(self, p):
        '''node : heading pernode APAGES lines protection populated'''
        p[0] = [p[1], p[2], p[4], p[5], p[6]]

    def p_populated(self, p):
        '''populated : PAGESETS NEWLINE cpus colonlines
                | lines PAGESETS NEWLINE cpus colonlines
                | empty'''
        if len(p) == 2:
            p[0] = []
        elif len(p) == 6:
            p[0] = [p[1], p[4], p[5]]
        else:
            p[0] = [p[3], p[4]]

    def p_pernode(self, p):
        '''pernode : PERNODE STATS NEWLINE lines
                   | empty'''
        p[0] = [] if len(p) == 2 else [p[1], p[4]]

    def p_protection(self, p):
        '''protection : PROTECTION COLON LPAREN numcommas NUMBER RPAREN NEWLINE
                | empty'''
        p[0] = [] if len(p) == 2 else p[4] + [p[5]]

    def p_numcomma(self, p):
        'numcomma : NUMBER COMMA'
        p[0] = p[1]

    def p_line(self, p):
        '''line : STRING NUMBER NEWLINE
                | NUMBER NEWLINE'''
        if len(p) == 4:
            p[0] = p[1:3]
        else:
            p[0] = p[1]

    def p_cpu(self, p):
        'cpu : CPU COLON NUMBER NEWLINE colonline colonline colonline \
                VM STATS THRESHOLD COLON NUMBER NEWLINE'

        p[0] = [p[3], p[5], p[6], p[7], [p[10], p[12]]]

    def p_colonline(self, p):
        'colonline : STRING COLON NUMBER NEWLINE'
        p[0] = [p[1], p[3]]

    def p_heading(self, p):
        'heading : NODE NUMBER COMMA ZONE STRING NEWLINE'
        p[0] = [p[2], p[5]]

    def get_path(self):
        return "/proc/zoneinfo"
