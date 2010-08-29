#! /usr/bin/python
r"""
FSM generator functors.
"""

rule_table  = { }

# A stack of sets of excluded states
excluded_states = [ set() ]

def exclude_state( f, exclude_list ):

	exclude_set = set(exclude_list)

	def _exclude( tokens ):
		for state in exclude_set:
			if state in excluded_states[-1]:
				raise StopIteration
		for i in f( tokens ):
			yield i

	return _exclude

def demand_state( f, demand_list ):

	demand_set = set(demand_list)

	def _demand( tokens ):
		for state in demand_set:
			if state not in excluded_states[-1]:
				raise StopIteration
		for i in f( tokens ):
			yield i

	return _demand

def free_state( f, free_list ):

	free_set = set(free_list)

	def _free( tokens ):
		excluded_states.append( excluded_states[-1].difference( free_set ) )
		for i in f( tokens ):
			yield i
		excluded_states.pop()

	return _free

def mark_state( f, mark_list ):

	mark_set = set(mark_list)

	def _mark( tokens ):
		excluded_states.append( excluded_states[-1].union( mark_set ) )
		for i in f( tokens ):
			yield i
		excluded_states.pop()

	return _mark

# Used as commands
state_command_map = {
						"^" : exclude_state,
						"&" : demand_state,
						"%" : free_state,
						"!" : mark_state,
					}

# Primitives
def nil_matcher():

	def _nil( tokens ):
		yield [None], tokens

	return _nil

def null_matcher():

	def _null( tokens ):
		raise StopIteration

	return _null

def consume_singleton( token ):

#	def _single( tokens ):
#		if tokens and tokens[0] == token:
#			yield [token], tokens[1:]

	def _single_lexed( tokens ):
		my_token, requirement = token, None
		if my_token[-1] == ";":
			my_token, requirement = my_token[:-1].split(";",1)
		if tokens and tokens[0][0] == my_token:
			# Interpret sequences like "operator;+;" as requiring 
			if requirement != None and tokens[0][1] != requirement:
				return
			yield [(my_token, tokens[0][1])], tokens[1:]

	return _single_lexed

	#return _single

def consume_stringleton( token ):

	def _stringle( tokens ):
		if tokens and tokens[:len(token)] == token:
			yield token, tokens[len(token):]

	return _stringle

def magic_markup( symbol_name ):

	def _magic_markup( tokens ):
		yield [symbol_name], tokens

	return _magic_markup

def consume_from_file( path ):

	lengths = { }

	openfile = open( path )

	for line in openfile:
		#line = line.split("#")[0].strip()
		line = line[:-1]
		if not line.strip(): continue
		line = lex(line)
		if len(line) not in lengths:
			lengths[len(line)] = set()
		lengths[len(line)].add(tuple(line))

	openfile.close()

	def _from_file( tokens ):
		for length in lengths:
			tup = tuple(tokens[:length])
			dataset = lengths[length]
			if len(tokens) >= length and tup in dataset:
				yield tokens[:length], tokens[length:]

	def _from_file_stringleton( tokens ):
		joined = "".join(tokens)
		for length in lengths:
			tup = tuple(joined)[:length]
			dataset = lengths[length]
			if len(joined) >= length and tup in dataset:
				yield [joined[:length]], list(joined[length:])

	if stringleton:
		return _from_file_stringleton
	else:
		return _from_file

def optional( f ):

	def _optional( tokens ):
		for i in f( tokens ):
			yield i
		yield [], tokens

	return _optional

def match_repeats( f ):

	def _reps( tokens ):
		for i in f( tokens ):
			yield i
			if i[0] != []:
			#if True:
				for j in _reps( i[1] ):
					yield i[0]+j[0], j[1]

	return _reps

def tag_at_same_time( f, tag ):

	def _tag( tokens ):
		for i in f( tokens ):
			if i[0] == []:
				yield ([], i[1])
			else:
				yield [(tag, i[0])], i[1]

	return _tag

def replace_tag( f, tag ):

	def _replace_tag( tokens ):
		for i in f( tokens ):
			if i[0] == []:
				yield ([], i[1])
			else:
				yield [(tag, i[0][0][1])], i[1]

	return _replace_tag

def strip_tag( f ):

	def _strip_tag( tokens ):
		for i in f( tokens ):
			if i[0] == []:
				yield ([], i[1])
			else:
				yield i[0][0][1], i[1]

	return _strip_tag

def no_tagging( f ):

	def _no_tagging( tokens ):
		for i in f( tokens ):
			if i[0] == []:
				yield ([], i[1])
			else:
				yield [None], i[1]

	return _no_tagging

def match_either( f, g ):

	def _either( tokens ):
		for i in f( tokens ):
			yield i
		for i in g( tokens ):
			yield i

	return _either

def chain( fs ):

	def chain_two( f, g ):

		def _chain( tokens ):
			for i in f( tokens ):
				#print f, i
				#print "Now entering:", g
				for j in g( i[1] ):
					#print "Final yield from chain:", i, j
					yield i[0]+j[0], j[1]

		return _chain

	return reduce( chain_two, fs )

rule_hits = { }
furthest_hit = None

def future_rule( rule_name ):

	def _dereference( tokens ):
		global furthest_hit

		# Used for finding syntax errors
		if furthest_hit == None or len(tokens) < furthest_hit:
			furthest_hit = len(tokens)

		# Used for profiling
		if rule_name not in rule_hits:
			rule_hits[ rule_name ] = 0
		rule_hits[ rule_name ] += 1

		#print "Dereferencing:", rule_name
		#print rule_table[rule_name]
		for i in rule_table[rule_name](tokens):
			#print "Yielding", i, rule_name
			yield i

	return _dereference

# Add plugins to mmp here!

from modes import *

