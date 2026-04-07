#!/bin/bash

scripts_dir=$(dirname "$0")
root_dir="$(dirname "$scripts_dir")"
root_dir=$(realpath "$root_dir")

py2bricks_dir="$root_dir/src/py2bricks"
py2bricks_dir=$(realpath "$py2bricks_dir")

# mandatory argument: script filename
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <llm-generated-script.py>"
    echo "Executes the given LLM-generated script, that will produce an LDraw .mpd model file"
    exit 1
fi

gen_script="$1"

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

# create a symlink to the py2bricks package in the same dir as the script, so that the script can import it
ln -s "$py2bricks_dir" "$gen_script_dir/py2bricks"

# remove the symlink on exit
trap "rm -f $gen_script_dir/py2bricks" EXIT

python "$gen_script_file"

