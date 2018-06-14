======
CosmEL
======

Author
------

* Mu Yang      <emfomy@gmail.com>
* Chi-Yen Chen <jina199312@gmail.com>
* Yi-Hui Lee   <lilyyhlee30@gmail.com>
* Wei-Yun Ma   <ma@iis.sinica.edu.tw>

Requirement
-----------

* `Python <http://www.python.org/>`_ 3.6.
* `PyTorch <http://pytorch.org/>`_ 0.4.0.
* `CKIPWS <http://otl.sinica.edu.tw/index.php?t=9&group_id=25&article_id=408>`_ Linux version.
* `CKIPParser <http://otl.sinica.edu.tw/index.php?t=9&group_id=25&article_id=1653>`_ Windows version.

Python Packages
"""""""""""""""
* `BeautifulSoup <http://www.crummy.com/software/BeautifulSoup/>`_ 4.6.
* `gensim <https://radimrehurek.com/gensim/>`_ 3.4.
* `lxml <http://lxml.de/>`_ 4.2.
* `NumPy <http://numpy.scipy.org/>`_ 1.14.
* `scikit-learn <http://scikit-learn.org/>`_ 0.19.
* `tqdm <https://pypi.org/project/tqdm/>`_ 4.23.

Documentation Packages
""""""""""""""""""""""
* `sphinx <http://www.sphinx-doc.org/>`_ 1.7.4.
* `sphinx_rtd_theme <https://github.com/rtfd/sphinx_rtd_theme/>`_ 0.3.1.
* `sphinxcontrib-programoutput <https://bitbucket.org/birkenfeld/sphinx-contrib>`_ 0.11.

Quick Start
-----------

Installation
""""""""""""

Install Conda
'''''''''''''

.. code-block:: bash

	wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
	sh Miniconda3-latest-Linux-x86_64.sh
	conda create -n cosmel python=3.6

Install Packages
''''''''''''''''

.. code-block:: bash

	source activate cosmel
	conda install pytorch=0.4.0 -c pytorch
	conda install beautifulsoup4=4.6 gensim=3.4 lxml=4.2 numpy=1.14 scikit-learn=0.19 tqdm=4.23


Example
"""""""

Enter Conda Environment
'''''''''''''''''''''''

.. code-block:: bash

	source activate cosmel
	cd <cosmel-root-path>

Database Generating
'''''''''''''''''''

.. code-block:: bash

	python3 ./util/database_generate.py -i data/input/styleme.csv -d data/demo/repo
	python3 ./util/database_generate.py -i data/input/styleme.csv -d data/demo/repo --etc

Training
''''''''

.. code-block:: bash

	python3 ./tool/corpusgen.py -c data/demo/corpus1 -d data/input/repo -i data/input/original_article1 -x data/demo/output/rid1
	python3 ./util/word2vec.py  -c data/demo/corpus1
	python3 ./tool/train.py     -c data/demo/corpus1 -m data/demo/model1 -x data/input/purged_article_gid_xml1


Predicting
''''''''''

.. code-block:: bash

	python3 ./tool/corpusgen.py -c data/demo/corpus2 -d data/input/repo -i data/input/original_article2 --rule-exact
	python3 ./tool/predict.py   -c data/demo/corpus2 -m data/demo/model1 -o data/demo/output/nid21
	python3 ./tool/predict.py   -c data/demo/corpus2 -m data/input/model0 -o data/demo/output/nid20
