
Multi-Modal Parser
==================

MMP is a parser which recursively descends BNF, with special states for other parsing algorithms which may be more efficient, or provide other information. For example, one may have a BNF "terminal" which drops into parsing with shunting-yard until it hits a delimiter.

MMP is also designed so that the naive implementation of a grammar will provide nice error messages.

The name is selected to be extremely unlikely to collide with any other projects.

Testing
-------

MMP comes with an example lexer file, lexer.rxl, and an example grammar file, grammar.bnf.
They specify the grammar for a pretend language, with a fairly complicated, but context free, grammar.
To test out the parser, try running pbnfpgp.py on the input file in inputs:

	python pbnfpgp.py inputs/example1.txt

The output should be a pretty-printed tree of the parsing of the input file.

Hackery
-------

Currently, the code invovles much hackery which will later be cleaned up, hopefully.

