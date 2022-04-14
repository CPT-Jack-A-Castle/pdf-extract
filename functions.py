import os
import string
import re
from ipaddress import ip_address
from urllib.parse import urlparse, ParseResult

import tldextract

MAIN_DIR = os.path.dirname(__file__)

def is_subdomain(domain,subdomain):
	"""
	Returns True if `subdomain` is a subdomain of `domain`, otherwise False.
	@param domain: the domain to check
	@type domain: str
	@param subdomain: the subdomain to check
	@type subdomain: str
	@rtype bool
	"""
	_domain_component = tldextract.extract(subdomain)
	
	_domain = _domain_component.domain
	_suffix = _domain_component.suffix
	
	_domain = _domain + '.' + _suffix
	domain = domain.rstrip('.')

	if domain == _domain:
		return True
	else:
		return False

def is_ipv4(addr,strict=True):
	"""
	Returns True if `addr` is an ipv4 address, otherwise False.
	@param addr: the addr to test for
	@type addr: str
	@param strict: specifies if the check should be strict or not. The default is True
	@type strict bool
	@rtype bool
	"""
	if strict:
		addr_component = addr.split('.')
		if len(addr_component) != 4:
			return False
		for comp in addr_component:
			if not comp.isnumeric():
				return False
			if not ( 0 <= int(comp) <= 255):
				return False
	try:
		assert ip_address(addr).version == 4
		return True
	except Exception:
		return False

def is_ipv6(addr,strict=True):
	"""
	Returns True if `addr` is an ipv6 address, otherwise False.
	@param addr: the addr to test
	@type addr: str
	@param strict: specifies if the check should be strict or not. The default is True
	@type strict bool
	@rtype bool
	"""
	addr = addr.replace('[','')
	addr = addr.replace(']','')

	if strict:
		required_chars = ':'
		allowed_chars = string.hexdigits + ':' + '.'

		if 0 == addr.count(':') > 7:
			return False

		for char in addr:
			if not char in allowed_chars:
				return False

	try:
		assert ip_address(addr).version == 6
		return True
	except Exception:
		return False

def is_domain(addr):
	"""
	Returns True if `addr` is a domain name, otherwise False.
	@param addr: the addr to test
	@type addr: str
	@rtype bool
	"""
	addr = addr.rstrip('.')
	allowed_chars = string.ascii_letters + string.digits + '-'
	
	if not addr or len(addr) > 255:
		return False

	labels = addr.split('.')
	for label in labels:
		if 0>= len(label) > 63:
			return False

		for char in label:
			if char not in allowed_chars:
				return False

	_domain_component = tldextract.extract(addr)

	_domain = _domain_component.domain
	_suffix = _domain_component.suffix

	if _domain and _suffix:
		return True
	else:
		return False

def is_ip(addr):
	"""
	Returns True if `addr` is an ipv4 or ipv6 address, otherwise False.
	@param addr: the addr to test
	@type addr: str
	@rtype bool
	"""

	if is_ipv4(addr):
		return True
	elif is_ipv6(addr):
		return True
	else:
		return False

def get_url_info(url):
	"""
	Returns a dict containing the sections in `url`.
	@param addr: the url to parse
	@type addr: str
	@rtype dict
	"""
	url = url.lstrip()
	parsed_url = urlparse(url)
	info = {
	'host':get_host_info(parsed_url.netloc).get('host'),'protocol':parsed_url.scheme,
	'query':parsed_url.query,'params':parsed_url.params,
	'fragment':parsed_url.fragment,'path':parsed_url.path
	}
	return info

def get_path_info(path):
	"""
	Returns a dict containing the directory, filename, and filename extension in `path`.
	@param path: the path to parse
	@type path: str
	@rtype dict
	"""
	path_component = os.path.splitext(path)
	p,ext = path_component
	filename = ''
	extension = ''
	if ext:
		dirname = os.path.dirname(p)
		basename = os.path.basename(p)
		if not dirname.endswith('/'):
			dirname += '/'
		_path = dirname
		filename = basename
	else:
		_path = path_component[0]
	extension = path_component[-1]
	return {'path':_path,'filename':filename,'extension':extension}

def is_domain_allowed(domain,accept,reject,allow_subdomain=True):
	"""
	Returns True if a domain is allowed, otherwise False.
	@param domain: the domain to check
	@type domain: str
	@param accept: the list of allowed domains
	@type accept: list
	@param reject: the list of unallowed domains
	@type reject: list
	@param allow_subdomain: specify whether wildcards should be ignored or acknowledged 
	in `accept` or `reject` list. The default is True
	@type allow_subdomain: bool
	@rtype: bool

	"""

	if domain.strip('.') in reject:
		return False

	for d in reject:

		if d.startswith('*') and not allow_subdomain:

			if is_subdomain(domain,d.lstrip('*.')):
				return False

		elif d.startswith('*'):
			d = d.lstrip('*.')
		
		if d == domain:
			return False

	for d in accept:
		if d.startswith('*') and not allow_subdomain:
			if is_subdomain(domain,d.lstrip('*.')):
				return True

		elif d.startswith('*'):
			d = d.lstrip('*.')

		if d == domain:
			return True

	return False

def is_ip_allowed(host,accept,reject):
	"""
	Returns True if `host` is allowed, otherwise False.
	@param host: an ip address to check against `accept` and `reject` lists
	@type host: str
	@param accept: a list containing allowed ip addresses
	@type accept: list
	@param reject: a list containing unallowed ip addresses
	@type reject: list
	@rtype bool
	"""
	if host in reject:
		return False
	elif host in accept:
		return True
	else:
		return False

def get_host_info(host, with_port=False):
	"""
	Returns a dictionary containing the username, password, host, and port section of `host`.
	@param host: the host to parse
	@type host: str
	@param with_port: specifies if port should also be parsed from the host. The default is False
	@type with_port: bool 
	"""
	sep = '@'
	username = ''
	password = ''
	port = ''
	_host = host
	
	try:
		if sep in host:
			creds,_host = host.split('@',1)
			if ':' in creds:
				username,password = creds.split(':',1)
			else:
				username = creds
	except Exception:
		_host = host
	finally:
		if ':' in _host and with_port:
			h_parts = _host.rsplit(':',1)
			if h_parts[-1].isnumeric():
				port = h_parts[-1]
				_host = h_parts[0]

		return {'username':username,'password':password,'host':_host,'port':port}

def create_url(scheme='', host='', path='', params='', query='', fragment=''):
	return ParseResult(scheme, host, path, params, query, fragment).geturl()

def get_protocol(url):
	url_parts = url.split(':', 1)
	if len(url_parts) == 2:
		protocol = url_parts[0]
		if protocol[0].isalpha() and protocol[-1].isalpha():
			allowed_chars = string.ascii_letters + '_' + '-' + string.digits
			for char in protocol:
				if not char in allowed_chars:
					return None
			return protocol
	return None

def is_valid_domain(domain_name):
	tld_file = os.path.join(MAIN_DIR, 'tlds.txt')

	domain_name_parts = domain_name.rsplit('.', 1)

	if len(domain_name_parts) < 2:
		return None
	else:
		tld = domain_name_parts[1].lower()

	with open(tld_file, 'rt') as f:
		for line in f:
			line = line.strip()
			if line and not line.startswith('#') and not line.startswith('//'):
				if line.lower() == tld:
					return True
	return False
