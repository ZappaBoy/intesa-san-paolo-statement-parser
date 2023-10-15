# intesa-san-paolo-statement-parser

`isparser` is a simple parser made to extract and convert the Intesa San Paolo PDF bank statement to csv.

## Installation

This tool uses [poetry](https://python-poetry.org/) to manage dependencies and packaging. To install all the
dependencies
simply run:

``` shell
poetry install
```

## Usage

You can run the tool using poetry:

``` shell
poetry run isparser --help
```

Or you can run the tool using python:

``` shell
python -m isparser --help
```

Or you can run the tool directly from the directory or add it to your path:

``` shell
isparser --help
```

```shell
usage: isparser [-h] [--verbose] [--debug] [--quiet | --no-quiet | -q] [--version] --files FILES [FILES ...] [--output OUTPUT] [--split | --no-split | -s] [--only-positive | --no-only-positive | -p]

isparser is a simple parser made to extract and convert the Intesa San Paolo PDF bank statement to csv.

options:
  -h, --help            show this help message and exit
  --verbose, -v         Increase verbosity. Use more than once to increase verbosity level (e.g. -vvv).
  --debug               Enable debug mode.
  --quiet, --no-quiet, -q
                        Do not print any output/log
  --version             Show version and exit.
  --files FILES [FILES ...], -f FILES [FILES ...]
                        Statement PDF file(s) to use
  --output OUTPUT, -o OUTPUT
                        Output CSV file path (Default: ./output.csv)
  --split, --no-split, -s
                        Split income and outcome movements in multiple files. Default: False
  --only-positive, --no-only-positive, -p
                        If --split is used, convert income and outcome to only positive numbers. Default: False
```

## Examples

### Parse single statement

``` shell
isparser -f "path/to/file.pdf"
```

### Parse multiple statements

``` shell
isparser -f "path/to/file.pdf" "path/to/second_file.pdf"
```

### Split income and outcome in two different files

``` shell
isparser -f "path/to/file.pdf" -s
```

### Practical example

```shell
isparser -f your/statements/path/Estratto\ conto\ trimestrale* -o movements.csv --split --only-positive
```