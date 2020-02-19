.. _SectionDataStructure:

Data Structure
==============

In CosmEL, we define some data structures for collecting cosmetics database, blog articles and CKIP tools relatively.


Repository
----------

To maintain the cosmetics database from PIXNET in an organized way, we create a data structure named :class:`.Repo`, containing several properties of :class:`.Brand` and :class:`.Product`.

**Brand** contains brand aliases for each brand. See more details in :class:`.Brand`.

**Product** has attributes of product ID, the corresponding brand, its product name, its product head word, and its description. Also, the product brand, name, and description have been word-segmented by CKIPWS tool and stored as segmented forms. A full product name can be split into four parts: **brand**, **infix**, **head word** and **suffix**.


Corpus
------

To preserve all information offered from PIXNET blog articles, we convert these information into several structured data objects. The main object :class:`.Corpus` contains information of mentions :class:`.MentionSet` and information of articles in both word segmented version :class:`.ArticleSet` and parsed version :class:`.ParsedArticleSet`.

**MentionSet**, consisting of all mentions in corpus, is constructed by :class:`.MentionBundleSet`, where a :class:`.MentionBundle` compromises all :class:`.Mention` in an :class:`.Article`. See more details in :class:`.MentionSet`.

An **Article** contains the information of an article, including its article ID, the parsed version of this article, and the bundle of mention set in this article. In addition, :class:`.ArticleSet` is the collection of :class:`.Article`. See more details in :class:`.Article`.

A **ParsedArticle** contains parsed sentences of the original **Article** and other information of the corresponding :class:`.Article`. Also, :class:`.ParsedArticleSet` is the collection of :class:`.ParsedArticle`. See more details in :class:`.ParsedArticle`.


Text and Word
-------------

All the texts are purged in our framework. Briefly, we convert them to lower cases, remove special symbols, remove spaces near non-alphabets, and replace spaces by '□'s. See more details in the source code of :class:`.PurgeString`.

In order to utilize CKIP tools, including word segmentation tool and parser, we also create several data structures, all collected in utility modules.

**WsWords** stores the result of segmented words as a :class:`list` of :class:`str`. Also, the PoS (part of speech) information and the role information (denoting the word roles --- brand, infix, and head) are stored as :class:`list`\ s of :class:`str`. See more detailed information in :class:`.WsWords`.


.. _XMLFormat:

XML Format
----------

We use XML/HTML tag to represent mention attributes.

Syntax:

.. code-block:: xml

   <product sid="SID" mid="MID" gid="GID" nid="NID" rid="RID" rule="RULE">MENTION</product>

Attribute Values:

   SID
      the sentence index in the article.

   MID
      the mention word index in the sentence.

   GID
      the golden ID (human labeled).

   NID
      the network-predicted ID.

   RID
      the rule-labeled ID.

   RULE
      the rule name.

   MENTION
      the mention word.


Take, the title of the article *part-00001/choyce96_324901572*, for example,

.. code-block:: xml

   巴黎萊雅限量玫瑰珍藏版訂製<product sid="0" mid="6" gid="6097" nid="" rid="6097" rule="P_rule1">唇膏</product>、
   奢華<product sid="0" mid="9" gid="4339" rid="OSP" rule="OSP_rule4">唇釉</product>新品體驗


Here we have two mentions, **唇膏** and **唇釉**.

   唇膏
      From the attributes, we know that the mention is the **6th** term of the **0th** sentence, linked to the **PID6097** product by the **P_rule1** rule, and linked to the **PID6097** product by human.

   唇釉
      From the attributes, we know that the mention is the **9th** term of the **0th** sentence, linked to an **Other Specific Product** by the **OSP_rule4** rule, and linked to the **PID4339** product by human.
