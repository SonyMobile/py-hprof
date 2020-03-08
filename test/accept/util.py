def progress(fname):
	last = (None, None)
	def cb(action, pos, end):
		if pos is None:
			print('%s: %s...                \r' % (fname, action), end='')
		elif end is None:
			print('%s: %s %d                \r' % (fname, action, pos), end='')
		else:
			nonlocal last
			percent = int(100 * pos / end)
			if last[0] != action or last[1] != percent:
				last = (action, percent)
				print('%s: %s %3d%%             \r' % (fname, action, percent), end='')
	return cb
