#!/usr/bin/python3
# Copyright 2016 The ANGLE Project Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#
# gen_format_map.py:
#  Code generation for GL format map. The format map matches between
#  {format,type} and internal format.
#  NOTE: don't run this script directly. Run scripts/run_code_generation.py.

import sys
import os

sys.path.append('renderer')
import angle_format

template_cpp = """// GENERATED FILE - DO NOT EDIT.
// Generated by {script_name} using data from {data_source_name}.
// ES3 format info from {es3_data_source_name}.
//
// Copyright 2016 The ANGLE Project Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
//
// format_map:
//   Determining the sized internal format from a (format,type) pair.
//   Also check es3 format combinations for validity.

#include "angle_gl.h"
#include "common/debug.h"

namespace gl
{{

GLenum GetSizedFormatInternal(GLenum format, GLenum type)
{{
    switch (format)
    {{
{format_cases}        case GL_NONE:
            return GL_NONE;

        default:
            break;
    }}

    return GL_NONE;
}}

bool ValidES3Format(GLenum format)
{{
    switch (format)
    {{
{es3_format_cases}            return true;

        default:
            return false;
    }}
}}

bool ValidES3Type(GLenum type)
{{
    switch (type)
    {{
{es3_type_cases}            return true;

        default:
            return false;
    }}
}}

bool ValidES3FormatCombination(GLenum format, GLenum type, GLenum internalFormat)
{{
    ASSERT(ValidES3Format(format) && ValidES3Type(type));

    switch (format)
    {{
{es3_combo_cases}        default:
            UNREACHABLE();
            break;
    }}

    return false;
}}

}}  // namespace gl
"""

template_format_case = """        case {format}:
            switch (type)
            {{
{type_cases}                default:
                    break;
            }}
            break;

"""

template_simple_case = """                case {key}:
                    return {result};
"""

template_es3_combo_type_case = """                case {type}:
                {{
                    switch (internalFormat)
                    {{
{internal_format_cases}                            return true;
                        default:
                            break;
                    }}
                    break;
                }}
"""


def parse_type_case(type, result):
    return template_simple_case.format(key=type, result=result)


def parse_format_case(format, type_map):
    type_cases = ""
    for type, internal_format in sorted(type_map.items()):
        type_cases += parse_type_case(type, internal_format)
    return template_format_case.format(format=format, type_cases=type_cases)


def main():

    # auto_script parameters.
    if len(sys.argv) > 1:
        inputs = [
            'renderer/angle_format.py', 'es3_format_type_combinations.json', 'format_map_data.json'
        ]
        outputs = ['format_map_autogen.cpp']

        if sys.argv[1] == 'inputs':
            print(','.join(inputs))
        elif sys.argv[1] == 'outputs':
            print(','.join(outputs))
        else:
            print('Invalid script parameters')
            return 1
        return 0

    input_script = 'format_map_data.json'

    format_map = angle_format.load_json(input_script)

    format_cases = ""

    for format, type_map in sorted(format_map.items()):
        format_cases += parse_format_case(format, type_map)

    combo_data_file = 'es3_format_type_combinations.json'
    es3_combo_data = angle_format.load_json(combo_data_file)
    combo_data = [combo for sublist in es3_combo_data.values() for combo in sublist]

    types = set()
    formats = set()
    combos = {}

    for internal_format, format, type in combo_data:
        types.update([type])
        formats.update([format])
        if format not in combos:
            combos[format] = {}
        if type not in combos[format]:
            combos[format][type] = [internal_format]
        else:
            combos[format][type] += [internal_format]

    es3_format_cases = ""

    for format in sorted(formats):
        es3_format_cases += "        case " + format + ":\n"

    es3_type_cases = ""

    for type in sorted(types):
        es3_type_cases += "        case " + type + ":\n"

    es3_combo_cases = ""

    for format, type_combos in sorted(combos.items()):
        this_type_cases = ""
        for type, combos in sorted(type_combos.items()):
            internal_format_cases = ""
            for internal_format in combos:
                internal_format_cases += "                        case " + internal_format + ":\n"

            this_type_cases += template_es3_combo_type_case.format(
                type=type, internal_format_cases=internal_format_cases)

        es3_combo_cases += template_format_case.format(format=format, type_cases=this_type_cases)

    with open('format_map_autogen.cpp', 'wt') as out_file:
        output_cpp = template_cpp.format(
            script_name=os.path.basename(sys.argv[0]),
            data_source_name=input_script,
            es3_data_source_name=combo_data_file,
            format_cases=format_cases,
            es3_format_cases=es3_format_cases,
            es3_type_cases=es3_type_cases,
            es3_combo_cases=es3_combo_cases)
        out_file.write(output_cpp)
    return 0


if __name__ == '__main__':
    sys.exit(main())
