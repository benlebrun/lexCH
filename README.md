# lexCH - Lexical Chainer



EXAMPLE COMMANDS AND USAGE INFORMATION
--------------------------------------

python get_senses.py < test/newstest2011.short.de.xml > test/newstest2011.short.senses.xml

python lexCH.py -s test/newstest2011.short.senses.xml -i test/newstest2011.short.de.xml -o test/newstest2011.chains.xml

mmax-import/mmax-xml-import.sh test/newstest2011.chains.xml mmax_chains


PUBLICATIONS
------------
The method is described in:

Laura Mascarell (2017): [Lexical Chains meet Word Embeddings in Document-level Statistical Machine Translation.](http://www.aclweb.org/anthology/W17-4813) In: Proceedings of the third Workshop on Discourse in Machine Translation. Copenhagen, Denmark.

Annette Rios Gonzales, Laura Mascarell, Rico Sennrich (2017): [Improving Word Sense Disambiguation in Neural Machine Translation with Sense Embeddings.](http://www.aclweb.org/anthology/W17-4702) In: Proceedings of the Second Conference on Machine Translation. Copenhagen, Denmark.
