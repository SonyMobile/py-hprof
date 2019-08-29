def dehex(s):
	s = s.replace(' ', '')
	return bytes(int(s[x:x+2], 16) for x in range(0, len(s), 2))
