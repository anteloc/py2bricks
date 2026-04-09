#!/bin/bash

scripts_dir=$(dirname "$0")
root_dir="$(dirname "$scripts_dir")"
root_dir=$(realpath "$root_dir")

py2bricks_dir="$root_dir/src/py2bricks"
py2bricks_dir=$(realpath "$py2bricks_dir")

# mandatory argument: script filename
if [ "$#" -lt 1 ]; then
    echo "Usage: $(basename "$0") <llm-generated-script.py> [--cmd '<printf template command>']"
    echo "Executes the given LLM-generated script, that will produce an LDraw .mpd model file, optionally executing a command on the generated .mpd file"
    echo "Examples:"
    echo "  $(basename "$0") generated_script.py --cmd 'cp %s /path/to/destination/'"
    echo "  $(basename "$0") generated_script.py --cmd 'open %s'"
    exit 1
fi

gen_script="$1"
shift

if [ "$1" == "--cmd" ]; then
    shift
    cmd_template="$1"
else
    cmd_template=""
fi

# if the script doesn't exist, exit with an error
if [ ! -f "$gen_script" ]; then
    echo "Error: file '$gen_script' not found"
    exit 1
fi

gen_script=$(realpath "$gen_script")

# get the dirname of the script, and change to that directory
gen_script_file="$(basename "$gen_script")"
gen_script_dir="$(dirname "$gen_script")"

cd "$gen_script_dir"

# create tmp file for script output, a convenience for post-processing the script output (e.g. to extract the generated .mpd filename)
tmp_output="$(mktemp)"
trap "rm -f $tmp_output" EXIT

python "$gen_script_file" 2>&1 | tee "$tmp_output"

# set -x
mpd_model="$(cat "$tmp_output" | grep -E '^Model created: (.+\.mpd)' | sed -E 's/Model created: (.+\.mpd)/\1/')"


if [ -n "$cmd_template" ]; then
    if [ -f "$mpd_model" ]; then
        cmd="$(printf "$cmd_template" "$mpd_model")"
        echo "Executing command: $cmd"
        eval "$cmd"
    else
        echo "Error: could not find generated .mpd model in script output"
        exit 1
    fi
fi

