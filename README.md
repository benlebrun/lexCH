# lexCH - Lexical Chainer

A tool to automatically obtain lexical chains from a document.

This is a project of the Computational Linguistics Group at the University of Zurich (http://www.cl.uzh.ch).

This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation.

REQUIREMENTS
------------
The software was developed on Linux using Python 2.7 and a version of the SenseGram tool that requires:  
numpy  
pandas<=0.17.1  
gensim>=0.13.1,<1.0

EXAMPLE COMMANDS AND USAGE INFORMATION
--------------------------------------

To obtain the lexical chains from a document, you first need to prepare the document (i.e. tokenize, lowercase/truecase...) and convert to XML file (see example ```test/newstest2011.short.de.xml```).

Train a sense model using SenseGram and update the path to the generated word and sense vectors in ```config.ini```. The quality of the model will impact on the quality of the detected lexical chains. 

The python script ```get_senses.py``` obtains the senses of the content words using SenseGram. 
```
python get_senses.py < test/newstest2011.short.de.xml > test/newstest2011.short.senses.xml
```

Obtain the lexical chains using the senses generated in the previous step. 
```
python lexCH.py -s test/newstest2011.short.senses.xml -i test/newstest2011.short.de.xml -o test/newstest2011.chains.xml
```

You can also use ```mmax-xml-import.sh``` to convert the lexical chains to MMAX format. 
```
mmax-import/mmax-xml-import.sh test/newstest2011.chains.xml mmax_chains
```

PUBLICATIONS
------------
The method is described in:

Laura Mascarell (2017): [Lexical Chains meet Word Embeddings in Document-level Statistical Machine Translation.](http://www.aclweb.org/anthology/W17-4813) In: Proceedings of the third Workshop on Discourse in Machine Translation. Copenhagen, Denmark.

Annette Rios Gonzales, Laura Mascarell, Rico Sennrich (2017): [Improving Word Sense Disambiguation in Neural Machine Translation with Sense Embeddings.](http://www.aclweb.org/anthology/W17-4702) In: Proceedings of the Second Conference on Machine Translation. Copenhagen, Denmark.
