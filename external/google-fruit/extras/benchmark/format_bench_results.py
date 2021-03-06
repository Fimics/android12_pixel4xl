#!/usr/bin/env python3
#  Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import json
from typing import Tuple, List, Dict, Union, Callable, Any, Sequence, Set, Iterable

import yaml
from collections import defaultdict

def extract_results(bench_results: List[Dict[str, Dict[Any, Any]]],
                    fixed_benchmark_params: Dict[str, Union[str, Tuple[str, ...]]],
                    column_dimension: str,
                    row_dimension: str,
                    result_dimension: str) -> Tuple[Dict[str, Dict[str, Dict[str, Any]]],
                                                    Set[Tuple[List[Tuple[str, str]], ...]],
                                                    Set[Tuple[Tuple[List[Tuple[str, str]], ...],
                                                              str]]]:
    table_data = defaultdict(lambda: dict())  # type: Dict[str, Dict[str, Dict[str, Any]]]
    remaining_dimensions_by_row_column = dict()
    used_bench_results = set()  # type: Set[Tuple[List[Tuple[str, str]], ...]]
    used_bench_result_values = set() # type: Set[Tuple[Tuple[List[Tuple[str, str]], ...], str]]
    for bench_result in bench_results:
        try:
            params = {dimension_name: make_immutable(dimension_value) 
                      for dimension_name, dimension_value in bench_result['benchmark'].items()}
            original_params = dict(params)
            results = bench_result['results']
            matches = True
            if result_dimension not in results:
                # result_dimension not found in this result, skip
                matches = False
            for param_name, param_value in fixed_benchmark_params.items():
                if (isinstance(param_value, tuple) and params.get(param_name) in param_value) or (params.get(param_name) == param_value):
                    pass
                else:
                    # fixed_benchmark_params not satisfied by this result, skip
                    matches = False
            if matches:
                # fixed_benchmark_params were satisfied by these params (and were removed)
                assert row_dimension in params.keys(), '%s not in %s' % (row_dimension, params.keys())
                assert column_dimension in params.keys(), '%s not in %s' % (column_dimension, params.keys())
                assert result_dimension in results, '%s not in %s' % (result_dimension, results)
                used_bench_results.add(tuple(sorted(original_params.items())))
                used_bench_result_values.add((tuple(sorted(original_params.items())),
                                              result_dimension))
                row_value = params[row_dimension]
                column_value = params[column_dimension]
                remaining_dimensions = params.copy()
                remaining_dimensions.pop(row_dimension)
                remaining_dimensions.pop(column_dimension)
                if column_value in table_data[row_value]:
                    previous_remaining_dimensions = remaining_dimensions_by_row_column[(row_value, column_value)]
                    raise Exception(
                        'Found multiple benchmark results with the same fixed benchmark params, benchmark param for row and benchmark param for column, so a result can\'t be uniquely determined. '
                        + 'Consider adding additional values in fixed_benchmark_params. Remaining dimensions:\n%s\nvs\n%s' % (
                            remaining_dimensions, previous_remaining_dimensions))
                table_data[row_value][column_value] = results[result_dimension]
                remaining_dimensions_by_row_column[(row_value, column_value)] = remaining_dimensions
        except Exception as e:
            raise Exception('While processing %s' % bench_result) from e
    return table_data, used_bench_results, used_bench_result_values

# Takes a 2-dimensional array (list of lists) and prints a markdown table with that content.
def print_markdown_table(table_data: List[List[str]]) -> None:
    max_content_length_by_column = [max([len(str(row[column_index])) for row in table_data])
                                    for column_index in range(len(table_data[0]))]
    for row_index in range(len(table_data)):
        row = table_data[row_index]
        cell_strings = []
        for column_index in range(len(row)):
            value = str(row[column_index])
            # E.g. if max_content_length_by_column=20, table_cell_format='%20s'
            table_cell_format = '%%%ss' % max_content_length_by_column[column_index]
            cell_strings += [table_cell_format % value]
        print('| ' + ' | '.join(cell_strings) + ' |')
        if row_index == 0:
            # Print the separator line, e.g. |---|-----|---|
            print('|-'
                  + '-|-'.join(['-' * max_content_length_by_column[column_index]
                                for column_index in range(len(row))])
                  + '-|')

# A sequence of length 2, with the lower and upper bound of the interval.
# TODO: use a class instead.
Interval = Sequence[float]

def compute_min_max(table_data, row_headers: List[str], column_headers: List[str]) -> Interval:
    values_by_row = {row_header: [table_data[row_header][column_header]
                                  for column_header in column_headers
                                  if column_header in table_data[row_header]]
                     for row_header in row_headers}
    # We compute min and max and pass it to the value pretty-printer, so that it can determine a unit that works well for all values in the table.
    min_in_table = min([min([min(interval[0][0], interval[1][0]) for interval in values_by_row[row_header]])
                        for row_header in row_headers])
    max_in_table = max([max([max(interval[0][1], interval[1][1]) for interval in values_by_row[row_header]])
                        for row_header in row_headers])
    return (min_in_table, max_in_table)

def pretty_print_percentage_difference(baseline_value: Interval, current_value: Interval):
    baseline_min = baseline_value[0]
    baseline_max = baseline_value[1]
    current_min = current_value[0]
    current_max = current_value[1]
    percentage_min = (current_min / baseline_max - 1) * 100
    percentage_max = (current_max / baseline_min - 1) * 100
    percentage_min_s = "%+.1f%%" % percentage_min
    percentage_max_s = "%+.1f%%" % percentage_max
    if percentage_min_s == percentage_max_s:
        return percentage_min_s
    else:
        return "%s - %s" % (percentage_min_s, percentage_max_s)

DimensionPrettyPrinter = Callable[[Any], str]

IntervalPrettyPrinter = Callable[[Interval, float, float], str]


# Takes a table as a dict of dicts (where each table_data[row_key][column_key] is a confidence interval) and prints it as a markdown table using
# the specified pretty print functions for column keys, row keys and values respectively.
# column_header_pretty_printer and row_header_pretty_printer must be functions taking a single value and returning the pretty-printed version.
# value_pretty_printer must be a function taking (value_confidence_interval, min_in_table, max_in_table).
# baseline_table_data is an optional table (similar to table_data) that contains the "before" state. If present, the values in two tables will be compared.
def print_confidence_intervals_table(table_name,
                                     table_data,
                                     baseline_table_data,
                                     column_header_pretty_printer: DimensionPrettyPrinter,
                                     row_header_pretty_printer: DimensionPrettyPrinter,
                                     value_pretty_printer: IntervalPrettyPrinter,
                                     row_sort_key: Callable[[Any], Any]):
    if table_data == {}:
        print('%s: (no data)' % table_name)
        return

    row_headers = sorted(list(table_data.keys()), key=row_sort_key)
    # We need to compute the union of the headers of all rows; some rows might be missing values for certain columns.
    column_headers = sorted(set().union(*[list(row_values.keys()) for row_values in table_data.values()]))
    if baseline_table_data:
        baseline_row_headers = sorted(list(baseline_table_data.keys()), key=row_sort_key)
        baseline_column_headers = sorted(set().union(*[list(row_values.keys()) for row_values in baseline_table_data.values()]))
        unmached_baseline_column_headers = set(baseline_row_headers) - set(row_headers)
        if unmached_baseline_column_headers:
            print('Found baseline column headers with no match in new results (they will be ignored): ', unmached_baseline_column_headers)
        unmached_baseline_row_headers = set(baseline_row_headers) - set(row_headers)
        if unmached_baseline_row_headers:
            print('Found baseline row headers with no match in new results (they will be ignored): ', unmached_baseline_row_headers)

    min_in_table, max_in_table = compute_min_max(table_data, row_headers, column_headers)
    if baseline_table_data:
        min_in_baseline_table, max_in_baseline_table = compute_min_max(table_data, row_headers, column_headers)
        min_in_table = min(min_in_table, min_in_baseline_table)
        max_in_table = max(max_in_table, max_in_baseline_table)

    table_content = []
    table_content.append([table_name] + [column_header_pretty_printer(column_header) for column_header in column_headers])
    for row_header in row_headers:
        row_content = [row_header_pretty_printer(row_header)]
        for column_header in column_headers:
            if column_header in table_data[row_header]:
                value = table_data[row_header][column_header]
                raw_confidence_interval, rounded_confidence_interval = value
                pretty_printed_value = value_pretty_printer(rounded_confidence_interval, min_in_table, max_in_table)
                if baseline_table_data and row_header in baseline_table_data and column_header in baseline_table_data[row_header]:
                    baseline_value = baseline_table_data[row_header][column_header]
                    raw_baseline_confidence_interval, rounded_baseline_confidence_interval = baseline_value
                    pretty_printed_baseline_value = value_pretty_printer(rounded_baseline_confidence_interval, min_in_table, max_in_table)
                    pretty_printed_percentage_difference = pretty_print_percentage_difference(raw_baseline_confidence_interval, raw_confidence_interval)
                    row_content.append("%s -> %s (%s)" % (pretty_printed_baseline_value, pretty_printed_value, pretty_printed_percentage_difference))
                else:
                    row_content.append(pretty_printed_value)
            else:
                row_content.append("N/A")
        table_content.append(row_content)
    print_markdown_table(table_content)


def format_string_pretty_printer(format_string: str) -> Callable[[str], str]:
    def pretty_print(s: str):
        return format_string % s

    return pretty_print

def float_to_str(x: float) -> str:
    if x > 100:
        return str(int(x))
    else:
        return '%.2g' % x

def interval_pretty_printer(interval: Interval, unit: str, multiplier: float) -> str:
    interval = list(interval)  # type: List[Any]
    interval[0] *= multiplier
    interval[1] *= multiplier

    # This prevents the format strings below from printing '.0' for numbers that already have 2 digits:
    # 23.0 -> 23
    # 2.0 -> 2.0 (here we don't remove the '.0' because printing just '2' might suggest a lower precision)
    if int(interval[0]) == interval[0] and interval[0] >= 10:
        interval[0] = int(interval[0])
    else:
        interval[0] = float_to_str(interval[0])
    if int(interval[1]) == interval[1] and interval[1] >= 10:
        interval[1] = int(interval[1])
    else:
        interval[1] = float_to_str(interval[1])

    if interval[0] == interval[1]:
        return '%s %s' % (interval[0], unit)
    else:
        return '%s-%s %s' % (interval[0], interval[1], unit)


# Finds the best unit to represent values in the range [min_value, max_value].
# The units must be specified as an ordered list [multiplier1, ..., multiplierN]
def find_best_unit(units: List[float], min_value: float, max_value: float) -> float:
    assert min_value <= max_value
    if max_value <= units[0]:
        return units[0]
    for i in range(len(units) - 1):
        if min_value > units[i] and max_value < units[i + 1]:
            return units[i]
    if min_value > units[-1]:
        return units[-1]
    # There is no unit that works very well for all values, first let's try relaxing the min constraint
    for i in range(len(units) - 1):
        if min_value > units[i] * 0.2 and max_value < units[i + 1]:
            return units[i]
    if min_value > units[-1] * 0.2:
        return units[-1]
    # That didn't work either, just use a unit that works well for the min values then
    for i in reversed(range(len(units))):
        if min_value > units[i]:
            return units[i]
    assert min_value <= min(units)
    # Pick the smallest unit
    return units[0]


def time_interval_pretty_printer(time_interval: Interval, min_in_table: float, max_in_table: float) -> str:
    sec = 1
    milli = 0.001
    micro = milli * milli
    units = [micro, milli, sec]
    unit_name_by_unit = {micro: '??s', milli: 'ms', sec: 's'}

    unit = find_best_unit(units, min_in_table, max_in_table)
    unit_name = unit_name_by_unit[unit]

    return interval_pretty_printer(time_interval, unit=unit_name, multiplier=1 / unit)


def file_size_interval_pretty_printer(file_size_interval: Interval, min_in_table: float, max_in_table: float) -> str:
    byte = 1
    kb = 1024
    mb = kb * kb
    units = [byte, kb, mb]
    unit_name_by_unit = {byte: 'bytes', kb: 'KB', mb: 'MB'}

    unit = find_best_unit(units, min_in_table, max_in_table)
    unit_name = unit_name_by_unit[unit]

    return interval_pretty_printer(file_size_interval, unit=unit_name, multiplier=1 / unit)


def make_immutable(x):
    if isinstance(x, list):
        return tuple(make_immutable(elem) for elem in x)
    return x


def dict_pretty_printer(dict_data: List[Dict[str, Union[str, Tuple[str]]]]) -> Callable[[Union[str, Tuple[str]]], str]:
    if isinstance(dict_data, list):
        dict_data = {make_immutable(mapping['from']): mapping['to'] for mapping in dict_data}

    def pretty_print(s: Union[str, Tuple[str]]) -> str:
        if s in dict_data:
            return dict_data[s]
        else:
            raise Exception('dict_pretty_printer(%s) can\'t handle the value %s' % (dict_data, s))

    return pretty_print



def determine_column_pretty_printer(pretty_printer_definition: Dict[str, Any]) -> DimensionPrettyPrinter:
    if 'format_string' in pretty_printer_definition:
        return format_string_pretty_printer(pretty_printer_definition['format_string'])

    if 'fixed_map' in pretty_printer_definition:
        return dict_pretty_printer(pretty_printer_definition['fixed_map'])

    raise Exception("Unrecognized pretty printer description: %s" % pretty_printer_definition)

def determine_row_pretty_printer(pretty_printer_definition: Dict[str, Any]) -> DimensionPrettyPrinter:
    return determine_column_pretty_printer(pretty_printer_definition)

def determine_row_sort_key(pretty_printer_definition: Dict[str, Any]) -> Callable[[Any], Any]:
    if 'fixed_map' in pretty_printer_definition:
        indexes = {x: i for i, x in enumerate(pretty_printer_definition['fixed_map'].keys())}
        return lambda s: indexes[s]

    return lambda x: x

def determine_value_pretty_printer(unit: str) -> IntervalPrettyPrinter:
    if unit == "seconds":
        return time_interval_pretty_printer
    if unit == "bytes":
        return file_size_interval_pretty_printer
    raise Exception("Unrecognized unit: %s" % unit)

def main():
    parser = argparse.ArgumentParser(description='Runs all the benchmarks whose results are on the Fruit website.')
    parser.add_argument('--benchmark-results',
                        help='The input file where benchmark results will be read from (1 per line, with each line in JSON format). You can use the run_benchmarks.py to run a benchmark and generate results in this format.')
    parser.add_argument('--baseline-benchmark-results',
                        help='Optional. If specified, compares this file (considered the "before" state) with the one specified in --benchmark-results.')
    parser.add_argument('--benchmark-tables-definition', help='The YAML file that defines the benchmark tables (e.g. fruit_wiki_bench_tables.yaml).')
    args = parser.parse_args()

    if args.benchmark_results is None:
        raise Exception("You must specify a benchmark results file using --benchmark-results.")

    if args.benchmark_tables_definition is None:
        raise Exception("You must specify a benchmark tables definition file using --benchmark-tables-definition.")

    with open(args.benchmark_results, 'r') as f:
        bench_results = [json.loads(line) for line in f.readlines()]

    if args.baseline_benchmark_results:
        with open(args.baseline_benchmark_results, 'r') as f:
            baseline_bench_results = [json.loads(line) for line in f.readlines()]
    else:
        baseline_bench_results = None

    with open(args.benchmark_tables_definition, 'r') as f:
        used_bench_results = set()
        # Set of (Benchmark definition, Benchmark result name) pairs
        used_bench_result_values = set()
        config = yaml.full_load(f)
        for table_definition in config["tables"]:
            try:
                fixed_benchmark_params = {dimension_name: make_immutable(dimension_value) for dimension_name, dimension_value in table_definition['benchmark_filter'].items()}
                table_data, last_used_bench_results, last_used_bench_result_values = extract_results(
                    bench_results,
                    fixed_benchmark_params=fixed_benchmark_params,
                    column_dimension=table_definition['columns']['dimension'],
                    row_dimension=table_definition['rows']['dimension'],
                    result_dimension=table_definition['results']['dimension'])
                used_bench_results = used_bench_results.union(last_used_bench_results)
                used_bench_result_values = used_bench_result_values.union(last_used_bench_result_values)
                if baseline_bench_results:
                    baseline_table_data, _, _ = extract_results(
                        baseline_bench_results,
                        fixed_benchmark_params=fixed_benchmark_params,
                        column_dimension=table_definition['columns']['dimension'],
                        row_dimension=table_definition['rows']['dimension'],
                        result_dimension=table_definition['results']['dimension'])
                else:
                    baseline_table_data = None
                rows_pretty_printer_definition = table_definition['rows']['pretty_printer']
                columns_pretty_printer_definition = table_definition['columns']['pretty_printer']
                results_unit = table_definition['results']['unit']
                print_confidence_intervals_table(table_definition['name'],
                                                 table_data,
                                                 baseline_table_data,
                                                 column_header_pretty_printer=determine_column_pretty_printer(columns_pretty_printer_definition),
                                                 row_header_pretty_printer=determine_row_pretty_printer(rows_pretty_printer_definition),
                                                 value_pretty_printer=determine_value_pretty_printer(results_unit),
                                                 row_sort_key=determine_row_sort_key(rows_pretty_printer_definition))
                print()
                print()
            except Exception as e:
                print('While processing table:\n%s' % table_definition)
                print()
                raise e
        allowed_unused_benchmarks = set(config.get('allowed_unused_benchmarks', []))
        allowed_unused_benchmark_results = set(config.get('allowed_unused_benchmark_results', []))
        for bench_result in bench_results:
            params = {dimension_name: make_immutable(dimension_value)
                      for dimension_name, dimension_value in bench_result['benchmark'].items()}
            benchmark_defn = tuple(sorted(params.items()))
            if benchmark_defn not in used_bench_results:
                if params['name'] not in allowed_unused_benchmarks:
                    print('Warning: benchmark result did not match any tables: %s' % params)
            else:
                unused_result_dimensions = {result_dimension
                                            for result_dimension in bench_result['results'].keys()
                                            if (benchmark_defn, result_dimension) not in used_bench_result_values and result_dimension not in allowed_unused_benchmark_results}
                if unused_result_dimensions:
                    print('Warning: unused result dimensions %s in benchmark result %s' % (unused_result_dimensions, params))


if __name__ == "__main__":
    main()
