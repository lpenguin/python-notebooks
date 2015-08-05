from collections import defaultdict

def read_obo(file_name):
	with open(file_name) as fd:
		fd_iter = _iter_lines(fd)
		header = _read_term(fd_iter)
		items = []
		typedefs = []
		for item_type in fd_iter:
			item = _read_term(fd_iter)
			if item_type == '[Term]':
				items.append(item)
			elif item_type == '[Typedef]':
				typedefs.append(item)

		return (header, items)

def _iter_terms(fd_iter):
	while True:
		yield _read_term(fd_iter)

def _iter_lines(fd):
	for line in fd:
		yield line.rstrip('\n')

def _read_term(fd_iter):
	res = defaultdict(list)
	for line in fd_iter:
		
		if not line:
			return res
		key, value = line.split(": ", 1)
		res[key].append(value.strip())


