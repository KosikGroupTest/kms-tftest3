import argparse
import json
import os

from pathlib import Path


def try_decode(args):
    try:
        return json.loads(args)
    except json.decoder.JSONDecodeError as e:
        ...
    possible_input_file = Path(args)
    assert possible_input_file.exists(), "Input needs to be file or JSON like string"
    assert possible_input_file.is_file(), "Input file is not a file, but directory"
    return json.load(possible_input_file.open())


def load_inputs():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir', help='directory to replace', default=".")
    parser.add_argument('--input', help='JSON file or JSON formated string that contains variables to be replaced')
    results = parser.parse_args()

    directory = Path(results.dir)
    try:
        data = try_decode(results.input)
        assert directory.exists(), "Input directory does not exist"
        assert directory.is_dir(), "Input directory does not exist"
    except json.decoder.JSONDecodeError as e:
        print(f"Invalid JSON: {e}")
        exit(1)
    except AssertionError as e:
        print(f"Invalid inputs: {e}")
        exit(1)
    return directory, data


def replace_in_string(string, data: dict):
    for key, value in data.items():
        if key.startswith("__"):
            continue
        string = string.replace(f"${{{key}}}", value)
    return string


def rename_file(file, data: dict) -> Path:
    if "${" in file.name:
        new_name = file.parent / replace_in_string(file.name, data)
        new_name.mkdir()
        os.rename(file, new_name)
        print(f"Renamed file {file.name} -> {new_name}")
        return new_name
    return file


def replace(input_dir, data: dict):
    ignore_files = data.get("__ignore__", [])
    ignore_files.append(".git")
    ignore_files.append(".venv")
    input_dir = rename_file(input_dir, data)

    for file in input_dir.iterdir():
        if file.name in ignore_files:
            continue
        if file.is_dir():
            replace(file, data)
        else:
            rename_file(file, data)
            print(f"Replacing {file}")
            file_content = replace_in_string(file.open().read(), data)
            file.write_text(file_content)


directory, inputs = load_inputs()
print(f"Replacing files in {directory}")
print(f"Using inputs {inputs}")
replace(directory, inputs)
