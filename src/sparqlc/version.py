from os.path import dirname, join

VERSION = open(join(dirname(dirname(__file__)), 'version.txt')).read().strip()
