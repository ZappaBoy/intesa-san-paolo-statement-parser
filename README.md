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