#!/bin/bash

scripts_dir=$(dirname "$0")
root_dir="$(dirname "$scripts_dir")"
root_dir=$(realpath "$root_dir")

py2bricks_dir="$root_dir/src/py2bricks"
examples_dir="$root_dir/examples"
dist_dir="$root_dir/dist"

mkdir -p "$dist_dir"

tmp_dir="$(mktemp -d)"
# trap "rm -rf $tmp_dir" EXIT
echo "Created temporary directory: $tmp_dir"

cp "$root_dir/instructions.md" "$tmp_dir/"
cp -r "$py2bricks_dir" "$tmp_dir/"
cp -r "$examples_dir" "$tmp_dir/"

# zip the contents of the tmp_dir into dist/llm-bundle-<timestamp>.zip
timestamp=$(date +%Y%m%d-%H%M%S)
zip_file="$dist_dir/llm-bundle-$timestamp.zip"

cd "$tmp_dir"

# cleanup
rm -rf py2bricks/__pycache__
rm examples/*.mpd

zip -r "$zip_file" ./*

echo "LLM bundle created: $zip_file"
