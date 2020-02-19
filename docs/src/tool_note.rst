.. _SectionToolNote:

Tool
====

.. _NoteDatabaseGeneration:

Database Generation
-------------------

To create database, one should provide a CSV file of products. This file should contains columns **編號**, **品牌**, **中文品名**, and **中文簡介**. Next run ``./util/database_generate.py``. It will automatic generate setting files in **<DATABASE>/etc/**.

   <DATABASE>/etc/brand0.txt
      the list of brand aliases. Each line corresponds to the aliases of a brand, separated by spaces.

   <DATABASE>/etc/head0.txt
      the list of head words. Each line corresponds to a head. One may refer the automatically generated file **head0.txt.auto** for modification.

   <DATABASE>/etc/compound0.txt
      the list of head word compounds. Each line corresponds to a compound and its word segmentation, separated by a tab.

   <DATABASE>/etc/core0.lex
      the core lexicon. Each line corresponds to a word and (optional) its post-tag, separated by a tab.

   <DATABASE>/etc/infix0.lex
      the infix lexicon. Each line corresponds to a word and (optional) its post-tag, separated by a tab.

   <DATABASE>/etc/product.head0
      the list of product heads. Each line corresponds to a product ID and its head, separated by a tab. One may refer the automatically generated file **product.head0.auto** for modification.

   <DATABASE>/etc/etc0.py
      an extra script, executed after loading each product from the CSV file. The data of the product is store in:

      * ``self.pid``:   編號
      * ``self.bname``: 品牌
      * ``self.pname``: 中文品名
      * ``self.descr``: 中文簡介

Please manually modify above files. After modification, run ``./util/database_generate.py`` again. Repeat modification and executing ``./util/database_generate.py`` until there is no error message.

.. seealso::

   * Specification - :ref:`SpecUtilDatabaseGeneration`
