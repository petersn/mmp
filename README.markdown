
Multi-Modal Parser
==================

MMP is a parser which recursively descends BNF, with special states for other parsing algorithms which may be more efficient, or provide other information. For example, one may have a BNF "terminal" which drops into parsing with shunting-yard until it hits a delimiter.

MMP is also designed so that the naive implementation of a grammar will provide nice error messages.

The name is selected to be extremely unlikely to collide with any other projects.

