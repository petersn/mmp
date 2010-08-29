#! /usr/bin/python
"""
Ad-hoc parsing algorithm (vaugely shunting-yard like) for expression parsing in MMP.

TODO: Make descriptions of operators and states be read in from an external file!
"""

version = "0001"

unaries  = set(("-", "not"))
binaries = set(("+=", "-=", "*=", "/=", "%=", "==", "!=", "+", "-", "*", "/", "<=", ">=", "=", "<", ">", "^", "and", "or"))

class Entry:
	def __init__(self, name):
		self.name = name

	def __str__(self):
		return self.name

binary_entries = { }

unary_entries  = { "-" : Entry("-"), "not" : Entry("not") }

unary_entries["-"].pres = 10
unary_entries["-"].arity = 1
unary_entries["-"].assoc = "left" # Not that it matters.
unary_entries["not"].pres = 3
unary_entries["not"].arity = 1
unary_entries["not"].assoc = "left" # Not that it matters.

operators = set( ("+", "-", "*", "/", ">", "<", "^", "%", "and", "or") )
lassoc = set( operators )
#operators.update( ( "=", "+=", "-=", "*=", "/=" ) )
operators.update( binaries )
rassoc = set( ("=", "+=", "-", "*=", "/=") )

pres = {
			"*" : 6, "/" : 6, "%" : 6,
			"+" : 5, "-" : 5,
			"<" : 4, ">" : 4, "^" : 4,
			"and" : 3, "or" : 3,
			"==" : 2, "!=" : 2, "<=" : 2, ">=" : 2,
			"=" : 1, "+=" : 1, "-=" : 1, "*=" : 1, "/=" : 1,
	   }

arity = {
		}

for operator in operators:
	arity[operator] = 2

for op in pres:
	entry = Entry(op)
	binary_entries[op] = entry
	entry.pres = pres[op]
	entry.arity = arity[op]
	entry.assoc = "left" if op in lassoc else "right"

onto_the_stack_with_you = set(("token", "integer", "float", "string"))

def complain( m ):
	print "Error:", m
	raise SystemExit

def genfunctor():
	return parse

def parse( t ):
	value_last = False
	output = []
	stack = []
	context = [ ("expr", stack) ]
	ptr = 0
	for typeof, token in t:
		ptr += 1
		if typeof in onto_the_stack_with_you:
			if value_last:
				#complain("Two values in a row. Perhaps missing an interstitial operator?")
				return
			output.append( (typeof, token, 0) )

			# Increment the argument counter
			if context[-1][0] == "call":
				context[-1][2] += 1

			value_last = True
		elif typeof == "operator":
			if value_last:
				if token not in binaries:
					#complain("Got an unary operator where only binaries are allowed.")
					return
				entry = binary_entries[token]
			else:
				if token not in unaries:
					#complain("Got a binary operator where only unaries are allowed.")
					return
				entry = unary_entries[token]
			while stack and ( (entry.assoc == "left" and entry.pres <= stack[-1].pres) or \
								(entry.assoc == "right" and entry.pres < stack[-1].pres) ):
				operator = stack.pop()
				output.append( ("operator", operator.name, operator.arity) )
			stack.append( entry )

			value_last = False
		elif typeof == "separator":
			if context[-1][0] != "call":
				#complain("Unwarranted comma not separating arguments to a function.")
				return
			value_last = False
		elif typeof == "open_paren":
			if value_last:
				stack = []
				context.append( ["call", stack, 0] )
			else:
				stack = []
				context.append( ("expr", stack) )
			value_last = False
		elif typeof == "close_paren":
			con = context.pop()
			while stack:
				operator = stack.pop()
				output.append( ("operator", operator.name, operator.arity) )
				if con[0] == "call":
					con[2] -= operator.arity-1
			if con[0] == "call":
				output.append( ("call", None, con[2]+1) )
			# Restore the previous operator stack
			stack = context[-1][1]
			value_last = True
		else:
			#complain("Unhandled token-type: %s Internal bug in the parser detected. Complain to Peter." % typeof)
			return
		if len(context) == 1:
			tmp_stack = stack[:]
			tmp_output = output[:]
			while tmp_stack:
				operator = tmp_stack.pop()
				tmp_output.append( ("operator", operator.name, operator.arity) )
			#print tmp_output
			tree = aritytree( tmp_output )
			if tree:
				yield (tree, t[ptr:])

#	if len(context) != 1:
#		#complain("Mismatched parens.")
#		return

#	while stack:
#		operator = stack.pop()
#		output.append( ("operator", operator.name, operator.arity) )

#	tree = aritytree( output )
#	if tree:
#		yield tree

	#return output

def aritytree( rpn ):
	pn = list(reversed(rpn))
	tree  = []
	stack = [ tree ]
	depths = []

	for typeof, token, arity in pn:
		if arity == 0:
			stack[-1].insert( 0, (typeof, token) )
			while stack and depths and len(stack[-1]) == depths[-1]:
				stack.pop()
				depths.pop()
		else:
			newlist = []
			stack[-1].insert( 0, ((typeof, token), newlist ) )
			stack.append( newlist )
			depths.append( arity )

	if depths:
		return None
		#complain( "Arity error: Operator still active at end of parsing." )

	return tree

if __name__ == "__main__":
	import lexer
	lex = lexer.Lexer("lexer.rxl")

	print "Shuntingyard demo."

	while True:
		inp = raw_input("> ")
		if not inp: continue
		tokens = lex( inp )
		print tokens
		rpn = parse( tokens )
		print rpn
		tree = aritytree( rpn )
		print tree

