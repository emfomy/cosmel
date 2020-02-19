.. _SectionUtilSpec:

Utility Specification
=====================


.. _SpecUtilArticlePreprocessing:

Article Preprocessing
---------------------

Purge the texts, and apply word segmentation.

Usage:

   .. program-output:: ./util/article_preprocess.py -h
      :cwd: ../..

Requirement:

   <CORPUS>/repo/
      the repository. [from :ref:`SpecUtilDatabaseGeneration`]

   <CORPUS>/html/original_article/
      the original articles. [from :ref:`SpecUtilHtmlPreprocessing`]

Output:

   <CORPUS>/html/purged_article/
      the purged articles.

   <CORPUS>/article/purged_article_ws_re#/
      the temporary word-segmented articles.

   <CORPUS>/article/bad_article.txt
      the list of bad articles (with too long sentences).


.. _SpecUtilArticlePostprocessing:

Article Postprocessing
----------------------

Add roles into word-segmented articles.

Usage:

   .. program-output:: ./util/article_postprocess.py -h
      :cwd: ../..

Requirement:

   <CORPUS>/repo/
      the repository. [from :ref:`SpecUtilDatabaseGeneration`]

   <CORPUS>/article/purged_article_ws_re#/
      the temporary word-segmented articles. [from :ref:`SpecUtilArticlePreprocessing`]

Output:

   <CORPUS>/article/purged_article_ws/
      the word-segmented articles.

   <CORPUS>/article/purged_article_role/
      the word-segmented articles with roles.


.. _SpecUtilHtmlDecoding:

HTML Decoding
-------------

Extract mentions from HTML.

Usage:

   .. program-output:: ./util/html_decode.py -h
      :cwd: ../..

Requirement:

   <CORPUS>/html/<INPUT>/
      the HTML files.

   <CORPUS>/article/purged_article_role/
      the word-segmented articles with roles. [from :ref:`SpecUtilArticlePostprocessing`]

   <CORPUS>/mention/purged_article/
      the mentions files. [from :ref:`SpecUtilMentionDetection`]

Output:

   <CORPUS>/mention/<OUTPUT>/
      the mention files.


.. _SpecUtilHtmlEncoding:

HTML Encoding
-------------

Embed mentions into HTML.

Usage:

   .. program-output:: ./util/html_encode.py -h
      :cwd: ../..

Requirement:

   <CORPUS>/html/html_article/
      the HTML files. [from :ref:`SpecUtilHtmlPreprocessing`]

   <CORPUS>/html/purged_article_idx/
      the index files. [from :ref:`SpecUtilHtmlPostprocessing`]

   <CORPUS>/mention/<INPUT>/
      the mention files.

Output:

   <CORPUS>/html/<OUTPUT>
      the encoded HTML files.


.. _SpecUtilHtmlExtracting:

HTML Extracting
---------------

Extract HTML articles from JSON sources.

Usage:

   .. program-output:: ./util/html_extract.py -h
      :cwd: ../..

Requirement:

   <CORPUS>/html/article_filtered/
      the JSON files.

Output:

   <CORPUS>/html/html_article/
      the HTML files.


.. _SpecUtilHtmlPreprocessing:

HTML Preprocessing
------------------

Extract texts from HTML articles.

Usage:

   .. program-output:: ./util/html_preprocess.py -h
      :cwd: ../..

Requirement:

   <CORPUS>/html/html_article/
      the HTML files. [from :ref:`SpecUtilHtmlExtracting`]

Output:

   <CORPUS>/html/html_article_notag/
      the HTML files without HTML tags.

   <CORPUS>/article/original_article/
      the text files extracted from above.


.. _SpecUtilHtmlPostprocessing:

HTML Postprocessing
-------------------

Indexing HTML with word-segmented articles.

Usage:

   .. program-output:: ./util/html_postprocess.py -h
      :cwd: ../..

Requirement:

   <CORPUS>/article/purged_article_role/
      the word-segmented articles with roles. [from :ref:`SpecUtilArticlePostprocessing`]

   <CORPUS>/html/html_article_notag/
      the HTML files without HTML tags. [from :ref:`SpecUtilHtmlPreprocessing`]

Output:

   <CORPUS>/html/purged_article_idx/
      the index files.


.. _SpecUtilMentionMerging:

Mention Merging
---------------

Merge the mentions.

Usage:

   .. program-output:: ./util/mention_detect.py -h
      :cwd: ../..

Requirement:

   <CORPUS>/mention/<BASE>/
      the base mentions files.

   <CORPUS>/mention/<INPUT>/
      the input mentions files.

Output:

   <CORPUS>/mention/<OUTPUT>/
      the output mentions files.


.. _SpecUtilMentionDetection:

Mention Detection
-----------------

Detect the mentions from articles.

Usage:

   .. program-output:: ./util/mention_detect.py -h
      :cwd: ../..

Requirement:

   <CORPUS>/article/purged_article_role/
      the word-segmented articles with roles. [from :ref:`SpecUtilArticlePostprocessing`]

Output:

   <CORPUS>/mention/purged_article/
      the mentions files.


.. _SpecUtilDatabaseGeneration:

Database Generation
-------------------

Generates the repository.

Usage:

   .. program-output:: ./util/database_generate.py -h
      :cwd: ../..

Requirement:

   <INPUT>
      the original purged CSV file.

   <DATABASE>/etc/
      the setting files.

Output:

   <DATABASE>/
      the repository files.


.. _SpecUtilRuleAnnotation:

Rule Annotation
---------------

Annotate the mentions by the rules.

Usage:

   .. program-output:: ./util/rule_exact.py -h
      :cwd: ../..

   .. program-output:: ./util/rule_parser.py -h
      :cwd: ../..

Requirement:

   <CORPUS>/article/purged_article_role/
      the word-segmented articles with roles. [from :ref:`SpecUtilArticlePostprocessing`]

   <CORPUS>/mention/purged_article
      the mentions files. [from :ref:`SpecUtilMentionDetection`]

Output:

   <CORPUS>/xml/purged_article_ws_rid/
      the rule-labeled XML articles.


.. _SpecUtilSentenceParsing:

Sentence Parsing
----------------

Parse the sentences.

Usage:

   .. program-output:: ./util/parse.py -h
      :cwd: ../..

Requirement:

   <CORPUS>/article/purged_article_ws_re<#>/
      the temporary word-segmented articles. [from :ref:`SpecUtilArticlePreprocessing`]

Output:

   <CORPUS>/article/parsed_article_parse/
      the parsed articles.


.. _SpecUtilWord2Vec:

Word2Vec
--------

Embed words using Word2Vec.

Usage:

   .. program-output:: ./util/word2vec.py -h
      :cwd: ../..

Requirement:

   <CORPUS>/repo/
      the repository. [from :ref:`SpecUtilDatabaseGeneration`]

   <CORPUS>/article/purged_article_role/
      the word-segmented articles with roles. [from :ref:`SpecUtilArticlePostprocessing`]

Output:

   <CORPUS>/embeddings/purged_article.dim300.emb.bin
      the embedding file.


.. _SpecUtilXmlDecoding:

XML Decoding
------------

Extract mentions from XML.

Usage:

   .. program-output:: ./util/xml_decode.py -h
      :cwd: ../..

Requirement:

   <CORPUS>/xml/<INPUT_WS>/
      the word-segmented XML files. [*optional*]

   <CORPUS>/xml/<INPUT>/
      the XML files. [*required if <INPUT_WS> is not set*]

   <CORPUS>/article/purged_article_role/
      the word-segmented articles with roles. [from :ref:`SpecUtilArticlePostprocessing`]

   <CORPUS>/mention/purged_article/
      the mentions files. [from :ref:`SpecUtilMentionDetection`]

Output:

   <CORPUS>/xml/<INPUT>
      the XML files. [*generated if <INPUT_WS> is set*]

   <CORPUS>/mention/<OUTPUT>/
      the mention files.


.. _SpecUtilXmlEncoding:

XML Encoding
------------

Encode articles and mentions into XML.

Usage:

   .. program-output:: ./util/xml_encode.py -h
      :cwd: ../..

Requirement:

   <CORPUS>/article/purged_article_role/
      the word-segmented articles with roles. [from :ref:`SpecUtilArticlePostprocessing`]

   <CORPUS>/mention/<INPUT>/
      the mention files.

Output:

   <CORPUS>/xml/<OUTPUT>/
      the encoded XML files.
