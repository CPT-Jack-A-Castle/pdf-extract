import os
import argparse
import json
import string
import re
from urllib.parse import urlparse

from functions import is_domain, is_subdomain, is_ip, get_protocol, is_valid_domain, get_url_info
import phonenumbers
import PyPDF2
from PyPDF2 import PdfFileReader

from io import StringIO

from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser

EXPECTED_EXTENSION = 'pdf'

"""
Add parallel processing of files.
"""

def get_cmd_args():
	parser = argparse.ArgumentParser()
	parser.add_argument('--file','-f', default=[], action='append', help='Specify the path of the pdf file.', dest='files')
	parser.add_argument('--directory', '-d', default=[], action='append', help='Specify the directory to get pdfs from.', dest='directories')
	parser.add_argument('--output', '-o', help='Specify the file to write the pdf metadata.', dest='output')
	parser.add_argument('--save', '-D', help='Specify the directory to write the metadata for each file.', dest='save_directory')
	parser.add_argument('--strict', '-s', action='store_true', help='Specify that only files with .pdf extension should be processed.', dest='strict')
	parser.add_argument('--verbose', '-v', default=0,action='count',help='verbosity rate.',dest='verbosity')
	args = parser.parse_args()
	return (args,parser)

def create_file_handle(filename, mode='rt'):
	file_handle = open(filename, encoding='utf-8',mode=mode)
	return file_handle

def close_file_handle(file_handle):
	try:
		if file_handle and hasattr(file_handle, 'close'):
			file_handle.close()
			return 1
	except Exception as e:
		print("[-] An Exception occurred while closing file handle: %s"%e)

	return 0

def get_files(directories, strict=False):

	files = set()

	for directory in directories:
		content = os.listdir(directory)
		for item in content:
			item = os.path.join(directory, item)
			if os.path.isfile(item):
				fn, extension = os.path.splitext(item)
				extension = extension.strip('.').lower()
				if strict and extension != EXPECTED_EXTENSION:
					continue
				else:
					files.add(os.path.abspath(item))
	
	return list(files)

def check_files(files):
	"""
	*files must be unique
	"""
	_files = []

	for file in files:
		if not os.path.exists(file):
			print("[-] File '%s' does not exists."%(file))
		elif not os.path.isfile(file):
			print("[-] File '%s' is not a valid file(it may be a directory)."%(file))
		else:
			_files.append(file)

	return _files

def check_directories(directories):
	"""
	*directories must be unique
	"""

	_directories = []

	for directory in directories:
		if not os.path.exists(directory):
			print("[-] Directory '%s' does not exists."%(directory))
		elif not os.path.isdir(directory):
			print("[-] Directory '%s' is not a valid directory(it may be a file)."%(directory))
		else:
			_directories.append(directory)

	return _directories

def get_info(path):
	
	_info = {}

	with open(path, 'rb') as f:
		pdf = PdfFileReader(f)
		info = pdf.getDocumentInfo()
		number_of_pages = pdf.getNumPages()
		xmp_metadata = pdf.getXmpMetadata()

		author = info.author
		creator = info.creator
		producer = info.producer
		subject = info.subject
		title = info.title

		for key in info:
			v = info[key]
			_info[key] = v

	return dict(_info)

def extract_text(path):
	output_string = StringIO()
	
	with open(path, 'rb') as in_file:
	    parser = PDFParser(in_file)
	    doc = PDFDocument(parser)
	    rsrcmgr = PDFResourceManager()
	    device = TextConverter(rsrcmgr, output_string, laparams=LAParams())
	    interpreter = PDFPageInterpreter(rsrcmgr, device)
	    for page in PDFPage.create_pages(doc):
	        interpreter.process_page(page)
	
	return output_string.getvalue()

def sanitize_filename(filename, _allowed_chars=''):
	
	allowed_chars = string.ascii_letters + string.digits + '-' + '_' + _allowed_chars
	_filename = ""
	for char in filename:
		if not char in allowed_chars:
			if _filename[-1:] == "_":
				char = ""
			else:
				char = "_"

		_filename += char

	return _filename.strip('_')

def extract_emails(text):
	
	"""
	Todo:
	1) Alter RegEx to match:
		username+alt-name@example.com
		user-name@example.com
		user_name@example.com
	"""

	regex = "((?:[a-zA-Z0-9\.]+(?:_)?[a-zA-Z0-9\.]+)(?:[\+](?:[a-zA-Z0-9\.]+(?:_)?[a-zA-Z0-9\.]+))?\@(?:[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+))"
	pattern = re.compile(regex)
	result = re.findall(pattern, text)
	return list(set(result))

def get_regions():
	with open('country_codes.json', 'rt') as f:
		cc = json.load(f)
		return cc

def extract_phonenumbers(text, region=None):
	phone_numbers = set()

	for match in phonenumbers.PhoneNumberMatcher(text, region, leniency=0):
		pn = match.raw_string
		phone_numbers.add(pn)

	return list(phone_numbers)

def extract_urls(text):

	regex = "(?:(?:[a-zA-Z]+):\/\/)?[\w/\-?=%.]+\.[\w/\-?=%.]+"
	pattern = re.compile(regex)
	urls = re.findall(pattern, text)	
	return list(set(urls))

def process_urls(urls):
	_urls = set()

	for url in urls:
		
		if not url:
			continue

		protocol = get_protocol(url)
		url = url.strip().strip('.')
		real_url = url
		# print(url, protocol)

		if protocol or url.startswith('//') or url.startswith('://'):
			url = urlparse(url).hostname

		if '/' in url:
			url = url.split('/', 1)
			url = url[0]


		if is_ip(url):
			_urls.add(real_url)
		elif is_domain(url):
			if is_valid_domain(url):
				_urls.add(real_url)

	return list(_urls)

def canonicalize_urls(urls, default_scheme='http'):
	_urls = set()
	for url in urls:
		if not url:
			continue

		if url.startswith('//'):
			url = default_scheme + ':' + url
		elif url.startswith('://'):
			url = default_scheme + url
		elif urlparse(url).scheme:
			pass
		else:
			url = default_scheme + ':' + '//' + url

		_urls.add(url)

	return list(_urls)

if __name__ == '__main__':

	args,parser = get_cmd_args()
	
	files = args.files
	directories = args.directories
	output = args.output
	save_directory = args.save_directory

	strict = args.strict
	verbosity = args.verbosity

	if not files and not directories:
		parser.error("either of the following arguments are required: --file, --directory/-d")

	if save_directory and not os.path.exists(save_directory):
		exit("[-] Directory '%s' to write the metadata files does not exist"%(save_directory))
	if save_directory and not os.path.isdir(save_directory):
		exit("[-] Directory '%s' is not a directory"%(save_directory))

	directories = check_directories(directories)
	files = check_files(files)

	files = [os.path.abspath(file) for file in files]

	files = set(files)
	dir_files = get_files(directories, strict)

	output_handle = None

	if output:
		output_handle = create_file_handle(output, mode='wt')

	for file in dir_files:
		files.add(file)

	metadata = {}

	try:
		for file in files:
			print("[+] Extracting metadata from file '%s'."%(file))
			try:
				if verbosity >= 3:
					print("[+] Extracting info from file '%s'."%(file))
				
				info = get_info(file)

				for key in info:
					val = info[key]
					if hasattr(val, 'decode'):
						val = val.decode('utf-8', errors='ignore')

					if type(val) != str:
						val = str(val)
					info[key] = val

				print(info)
				
				if verbosity >= 3:
					print("[+] Extracting text from file '%s'."%(file))
				
				text = extract_text(file)
				
				if verbosity >= 3:
					print("[+] Extracting telephone numbers from file '%s'."%(file))
				
				phone_numbers = extract_phonenumbers(text)
				
				if verbosity >= 3:
					print("[+] Extracting emails from file '%s'."%(file))
				
				emails = extract_emails(text)
				
				if verbosity >= 3:
					print("[+] Extracting urls from file '%s'."%(file))
				
				urls = extract_urls(text)
				urls = process_urls(urls)
				urls = canonicalize_urls(urls)
				metadata[file] = {'info':info, 'phone_numbers':phone_numbers, 'emails':emails, 'urls':urls}
			except Exception as e:
				print("[-] An exception occurred while processing file: %s"%(e))
				continue

			if verbosity > 0:
				print("[%s]"%(file))
				print(info)
				print(json.dumps(info, indent=2))
				print()
				print()
	except KeyboardInterrupt:
		pass

	
	if output_handle:
		#dump all metadata in one file
		print("[+] Dumping metadata into file '%s'."%(output))
		json.dump(metadata, output_handle, indent=2)
		print("[+] Metadata has been dumped successfully into file '%s'."%(output))
		close_file_handle(output_handle)
	
	if save_directory:
		print("[+] Dumping metadata into their respective files.")
		for filename in metadata:
			fname = sanitize_filename( os.path.basename(filename), '.')
			fname += '.json'
			fname = os.path.join(save_directory, fname)

			mdata = metadata[filename]
			
			f_handle = create_file_handle(fname, 'wt')
			json.dump(mdata, f_handle, indent=2)
			close_file_handle(f_handle)

			print("[+] Metadata for file '%s' has been dumped successfully into file '%s'."%(filename, fname))

	if verbosity >= 3:
		print(json.dumps(metadata, indent=2))