CosmEL
======


Author
------

`CKIP Lab <http://ckip.iis.sinica.edu.tw/>`_, Institute of Information Science, Academia Sinica, Taipei, Taiwan.

* Mu Yang      <emfomy@gmail.com>
* Chi-Yen Chen <jina199312@gmail.com>
* Yi-Hui Lee   <lilyyhlee30@gmail.com>
* Wei-Yun Ma   <ma@iis.sinica.edu.tw>


Requirement
-----------

* `Python <http://www.python.org/>`_ 3.6.
* `PyTorch <http://pytorch.org/>`_ 0.4.0.
* `CKIPWS <http://otl.sinica.edu.tw/index.php?t=9&group_id=25&article_id=408>`_ Linux version.
* `CKIPParser <http://otl.sinica.edu.tw/index.php?t=9&group_id=25&article_id=1653>`_ Windows version. (Optional)

Python Packages
^^^^^^^^^^^^^^^
* `BeautifulSoup <http://www.crummy.com/software/BeautifulSoup/>`_ 4.6.
* `gensim <https://radimrehurek.com/gensim/>`_ 3.4.
* `lxml <http://lxml.de/>`_ 4.2.
* `NumPy <http://numpy.scipy.org/>`_ 1.14.
* `scikit-learn <http://scikit-learn.org/>`_ 0.19.
* `tqdm <https://pypi.org/project/tqdm/>`_ 4.23.

Documentation Packages
^^^^^^^^^^^^^^^^^^^^^^
* `sphinx <http://www.sphinx-doc.org/>`_ 1.7.4.
* `sphinx_rtd_theme <https://github.com/rtfd/sphinx_rtd_theme/>`_ 0.3.1.
* `sphinxcontrib-programoutput <https://bitbucket.org/birkenfeld/sphinx-contrib>`_ 0.11.


Installation
------------

Install Conda
^^^^^^^^^^^^^

First install the Conda environment. Conda is an open source package management system. It quickly installs, runs and updates packages and their dependencies.

.. code-block:: bash

   wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
   sh ./Miniconda3-latest-Linux-x86_64.sh

Make sure to prepend the Miniconda3 install location to ``PATH`` in your ``.bashrc``. Now restart your shell to enable ``PATH``, or export it manually:

.. code-block:: bash

   export PATH="$HOME/miniconda3/bin:$PATH"

Next, create a new Conda environment for CosmEL, named **cosmel**, with Python version 3.6.

.. code-block:: bash

   conda create -n cosmel python=3.6


Install Packages
^^^^^^^^^^^^^^^^

First activate the CosmEL Conda environment:

.. code-block:: bash

   source activate cosmel

Now, ``(cosmel)`` will be appended to the prompt string:

.. code-block:: console

   (cosmel) <user>@<host>:~$

Next, install the Python packages:

.. code-block:: bash

   conda install python=3.6.2 -c intel
   conda install pytorch=0.4.0 -c pytorch -c intel
   conda install beautifulsoup4=4.6 gensim=3.4 lxml=4.2 numpy=1.14 scikit-learn=0.19 tqdm=4.23 -c intel


CKIPWS
^^^^^^

Denote the root path of CosmEL (the folder containing this README) as ``<cosmel-root>``, and the root path of CKIPWS as ``<ckipws-root>``. Copy the following files:

.. code-block:: bash

   cp <ckipws-root>/lib/libWordSeg.so <cosmel-root>/libWordSeg.so
   cp <ckipws-root>/Data2             <cosmel-root>/Data2 -r

You may add ``<ckipws-root>/lib/`` to ``LD_LIBRARY_PATH`` instead of copying ``libWordSeg.so``.


CKIPParser (Optional)
^^^^^^^^^^^^^^^^^^^^^

At Windows Server
"""""""""""""""""

Denote the root path of CKIPParser as ``<ckipparser-root>``. Then,

.. code-block:: bat

   cd <ckipparser-root>
   copy <ckipws-root>\parser\CKIPParser_Socket_Server.py .\CKIPParser_Socket_Server.py
   copy <ckipws-root>\parser\parser.ini                  .\parser.ini
   python3 .\CKIPParser_Socket_Server.py


At Linux Client
"""""""""""""""

Modify ``<cosmel-root>/util.rule_parser`` by replacing ``host = '172.16.1.64'`` by the IP of the Windows server.


Example
-------

Enter Conda Environment
^^^^^^^^^^^^^^^^^^^^^^^

Remember to activate the CosmEL Conda environment if not activated. Goto the root path of CosmEL (``<cosmel-root>``, the folder containing this README), and create the working space for this example (``data/demo/``).

.. code-block:: bash

   source activate cosmel
   cd <cosmel-root>
   mkdir -p data/demo


Database Generation
^^^^^^^^^^^^^^^^^^^

Generate database from ``demo/styleme.csv``:

.. code-block:: bash

   python3 ./util/database_generate.py -i demo/styleme.csv -d data/demo/repo

You can modify ``data/demo/repo/etc/`` to ameliorate the database. See :ref:`IntroDatabaseGeneration` for details. You may also use the predefined database by adding ``--etc``:

.. code-block:: bash

   python3 ./util/database_generate.py -i demo/styleme.csv -d data/demo/repo --etc

The database are stored in ``data/demo/repo/``.

See more details in :ref:`UsageDatabaseGeneration`.


Training
^^^^^^^^

In training step, first generate the corpus (``data/demo/corpus1/``) from the articles (``demo/original_article1/``). Here ``demo/repo/`` is used as database.

.. code-block:: bash

   python3 ./tool/corpusgen.py -c data/demo/corpus1 -d demo/repo -i demo/original_article1 -x data/demo/output/rid1

If you have CKIPParser, you may add ``--rule-parser`` to use parser-based rule annotation:

.. code-block:: bash

   python3 ./tool/corpusgen.py -c data/demo/corpus1 -d demo/repo -i demo/original_article1 -x data/demo/output/rid1 --rule-parser

The rule-labeled articles are exported to ``data/demo/output/rid1/``. You may modify the ``gid`` flags in these files for manually annotation. Here we provide some manually labeled files in ``demo/purged_article_gid_xml1/``.

Next, you may train word embeddings from the corpus (stored in ``data/demo/corpus1/embeddings/``):

.. code-block:: bash

   python3 ./util/word2vec.py -c data/demo/corpus1


Or use other embeddings, but make sure that all brand aliases are contained in this embeddings.

Finally, train the model using the corpus (``data/demo/corpus1/``), with manually-labeled articles ``demo/purged_article_gid_xml1/`` and embeddings file ``demo/emb1.bin``:

.. code-block:: bash

   python3 ./tool/train.py -c data/demo/corpus1 -m data/demo/model1 -x demo/purged_article_gid_xml1 --emb demo/emb1.bin

The model data are stored in ``data/demo/model1/``.

See more details in :ref:`UsageToolCorpusGeneration`, :ref:`UsageToolTraining`, and :ref:`UsageWord2Vec`.


Prediction
^^^^^^^^^^

In prediction step, first generate the corpus (``data/demo/corpus2/``) from the articles (``demo/original_article2/``). Here ``demo/repo/`` is used as database.

.. code-block:: bash

   python3 ./tool/corpusgen.py -c data/demo/corpus2 -d demo/repo -i demo/original_article2

Next, predict the labels of the corpus (``data/demo/corpus2/``) with model ``data/demo/model1/``.

.. code-block:: bash

   python3 ./tool/predict.py -c data/demo/corpus2 -m data/demo/model1 -o data/demo/output/nid2

The results are exported to ``data/demo/output/nid2/``.

See more details in :ref:`UsageToolCorpusGeneration` and :ref:`UsageToolPrediction`.


Documentation
-------------

To build the documentation, please install the following packages.

.. code-block:: bash

   cd <cosmel-root>/docs
   conda install sphinx=1.7.4 sphinx_rtd_theme=0.3.1
   conda install sphinxcontrib-programoutput=0.11 -c conda-forge

Next, build the HTML documentation.

.. code-block:: bash

   make html

The outputs are located in ``<cosmel-root>/docs/_build/html/``.

You may also build PDF documentation using LaTeX if you have ``latexmk`` and ``xelatex`` installed.

.. code-block:: bash

   make latex

The outputs are located in ``<cosmel-root>/docs/_build/latex/``.
