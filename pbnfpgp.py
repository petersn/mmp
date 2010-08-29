#! /usr/bin/python
"""
pbnfpgp: Peter's Backus Naor Form Parser Generator Parser

Reads in an input description of a parser, and produces an mmp parser generator
"""

import parser
from parser import *

# Used for path calculations for the include-file directive.
import os

escapes = {
			"\\\\" : "\\",
			"\\n"  : "\n",
			"\\s"  : " ",
			"\\t"  : "	",
			"\\h"  : "#",
			"\\q"  : '"',
			"\\p"  : "|",
		  }

def splitup( x ):
	x = x.split("|")
	x = [ i.split(" ") for i in x ]
	for i in x:
		while "" in i:
			i.remove("")
	return x

def process_escapes( symbol ):
	for start, end in escapes.items():
		symbol = symbol.replace(start, end)
	return symbol

def load_file( path ):
	global rule_table

	definitions = { }

	openfile = open( path )
	data = openfile.read()
	openfile.close()

	data = data.replace("\t", " ")
	data = data.replace("\\\n", "")

	for line in data.split("\n"):
		line = line.split("#")[0].strip()
		if not line: continue

		if line.startswith("include-file "):
			line = line[13:]
			path = os.path.abspath( os.path.expanduser( line.strip() ) )
			directory = os.path.dirname( path )

			cwd = os.getcwd()
			os.chdir( directory )
			load_file( path )
			os.chdir( cwd )
			continue

		lhs, rhs = line.split("=", 1)

		lhs = lhs.strip()

		rhs = splitup(rhs)

		definitions[lhs] = rhs

	for lhs, rhs in definitions.items():
		generator, name = compile_matcher( lhs, rhs )
		rule_table[name] = generator

def encase( generator, enum="1" ):
	if enum == "?":
		generator = optional( generator )
	elif enum == "...":
		generator = optional( match_repeats( generator ) )
	elif enum == "+":
		generator = match_repeats( generator )
	return generator

stringleton = False

def compile_matcher( name, rule ):
	def single_compile_matcher( rule ):
		state_checkers = []

		# Remove any state exclusions, freeings, or markings that might appear in the rule
		while rule[0][0] in state_command_map:
			if state_checkers and state_checkers[-1][0] == rule[0][0]:
				state_checkers[-1][1].append( rule.pop(0)[1:] )
			else:
				state_checkers.append( (rule[0][0], [ rule.pop(0)[1:] ] ) )

		sub_matchers = []
		for symbol in rule:
			tag	   = None
			invisible = False
			enum	  = "1"

			# First, process all the special markups
			while True:
				if (not symbol.startswith('"')) and ":" in symbol:
					symbol, tag = symbol.rsplit(":", 1)
					continue
				if symbol.endswith("?"):
					enum = "?"
					symbol = symbol[:-1]
					continue
				if symbol.endswith("..."):
					enum = "..."
					symbol = symbol[:-3]
					continue
				if symbol.endswith("+"):
					enum = "+"
					symbol = symbol[:-1]
					continue
				if symbol.endswith("~"):
					invisible = True
					symbol = symbol[:-1]
					continue
				break

			# String literal; "abc"
			if symbol[0] == '"' and symbol[-1] == '"':
				if stringleton:
					generator = encase( consume_stringleton( list( process_escapes(symbol[1:-1]) ) ), enum )
				else:
					generator = encase( consume_singleton( process_escapes(symbol[1:-1]) ), enum )
				if tag:
					generator = tag_at_same_time( generator, tag )
				if invisible:
					generator = no_tagging( generator )
				sub_matchers.append( generator )

			# Markup symbol; (name)
			elif symbol[0] == "(" and symbol[-1] == ")":
				if enum != "1":
					print "Warning: Placing an enum on a markup symbol makes no sense."
				generator = magic_markup( symbol[1:-1] )
				if tag:
					generator = tag_at_same_time( generator, tag )
				if invisible:
					print "Warning: Making an invisible markup symbol is pointless."
				sub_matchers.append( generator )

			# File expansion; file@lists/nouns.lst
			elif symbol.startswith("file@"):
				generator = encase( consume_from_file( os.path.expanduser( symbol[5:] ) ), enum )
				if tag:
					generator = tag_at_same_time( generator, tag )
				if invisible:
					generator = no_tagging( generator )
				sub_matchers.append( generator )

			# Nil rule, that matches everything immediately, consuming no tokens; nil
			elif symbol == "nil":
				if enum != "1":
					print "Warning: Placing an enum on a nil symbol makes no sense."
				if invisible:
					print "Warning: An invisible nil symbol makes no sense, as nils return no tree."
				generator = nil_matcher()
				sub_matchers.append( generator )

			# Null rule, that matches nothing; null
			elif symbol == "null":
				if enum != "1":
					print "Warning: Placing an enum on a null symbol makes no sense."
				if invisible:
					print "Warning: An invisible null symbol makes no sense, as nulls don't return."
				generator = null_matcher()
				sub_matchers.append( generator )

			# External parsing mode
			elif symbol.startswith("ext~"):
				generator = getattr( parser, symbol[4:] )()
				generator = encase( generator, enum )
				if tag:
					generator = replace_tag( generator, tag )
				elif tag != None:
					generator = strip_tag( generator )
				if invisible:
					generator = no_tagging( generator )
				sub_matchers.append( generator )

			# Rule reference; rule
			else:
				generator = encase( future_rule( symbol ), enum )
				if tag:
					generator = replace_tag( generator, tag )
				elif tag != None:
					generator = strip_tag( generator )
				if invisible:
					generator = no_tagging( generator )
				sub_matchers.append( generator )

		generator = chain( sub_matchers )

		for check, var_list in reversed(state_checkers):
			generator = state_command_map[check]( generator, var_list )

		return generator

	generator = reduce( match_either, (single_compile_matcher( subrule ) for subrule in rule) )

	tag = name

	if ":" in name:
		name, tag = name.rsplit(":", 1)

	if tag:
		generator = tag_at_same_time( generator, name )

	return generator, name

def indent( s, spaces=4 ):
	return "\n".join( i if not i.strip() else (" "*spaces)+i for i in s.split("\n") )

def pretty( x ):
	if type(x) == str:
		return '"%s"\n' % x
	elif x == None:
		return ""
	output = ""

	if type(x) == list:
		output += "{\n"
		for v in x:
			output += indent( pretty( v ), 2 )
		output += "}\n"
		return output

	name, sub = x
	# Hack hack hack to make this pretty printer work.
	# Avert your gaze for the next few if statements.
	if name == ("call", None):
		name = "call"
	if type(name) == tuple:
		output += "{\n"
		for v in x:
			output += indent( pretty( v ), 2 )
		output += "}\n"
		return output
	if stringleton and all( type(i) == str for i in sub ):
		sub = ["".join(sub)]
	if type(sub) == str:
		return "%s: %s\n" % (name, sub)
	if len(sub) == 1 and type(sub[0]) == str:
		return "%s: %s\n" % (name, sub[0])
	output += name+" {\n"
	for v in sub:
		output += indent( pretty( v ), 2 )
	output += "}\n"
	return output

def clean_up( x ):
	"""Takes a parsed tree, and cleans up Nones lying about, and concatenates characters if you are running in stringle mode."""
	if type(x) == str:
		return x
	name, sub = x
	if type(sub) == str:
		return x
	if stringleton and all( type(i) == str for i in sub ):
		sub = ["".join(sub)]
	else:
		sub = [ clean_up(i) for i in sub if i != None ]
	return (name, sub)

def parse( statement ):
	statement = lex(statement)

	valid = []
	for parsing in rule_table["main"]( statement ):
		if parsing[1] == []:
			valid.append( parsing[0][0] )

	valid = [ clean_up(i) for i in valid ]

	return valid

if __name__ == "__main__":

	try:
		import lexer
		lex = lexer.Lexer("lexer.rxl")
	except Exception, e:
		print "Error:", e
		print "Create a lexer.rxl in the local directory, then try again."
		raise SystemExit

	try:
		load_file("grammar.bnf")
	except Exception, e:
		print "Error:", e
		print "Create a grammar.bnf file in the local directory, then try again."
		raise SystemExit

	import sys

	# Parse input files, if given as arguments
	for path in sys.argv[1:]:
		data = open(path).read()

		for parsing in parse( data ):
			print parsing
			print pretty( parsing )

	if sys.argv[1:]:
		raise SystemExit

	# Otherwise, interactively allow the user to play with the parser
	while True:
		statement = raw_input(">")

		for parsing in parse( statement ):
			print parsing
			print pretty(parsing)

