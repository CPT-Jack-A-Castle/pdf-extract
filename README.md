# pdf-extract
Extract metadata, phone numbers, emails, and links from PDF files


## Install the required files

```
pip install -r requirements.txt
```

## Usage

```
python pdf_extract.py --help
```

```
usage: pdf_extract.py [-h] [--file FILES] [--directory DIRECTORIES] [--output OUTPUT] [--save SAVE_DIRECTORY] [--strict] [--verbose]

optional arguments:
  -h, --help            show this help message and exit
  --file FILES, -f FILES
                        Specify the path of the pdf file.
  --directory DIRECTORIES, -d DIRECTORIES
                        Specify the directory to get pdfs from.
  --output OUTPUT, -o OUTPUT
                        Specify the file to write the pdf metadata.
  --save SAVE_DIRECTORY, -D SAVE_DIRECTORY
                        Specify the directory to write the metadata for each file.
  --strict, -s          Specify that only files with .pdf extension should be processed.
  --verbose, -v         verbosity rate.

```
