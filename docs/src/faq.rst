.. _SectionFAQ:

FAQ
===

* The CKIPWS crashed with error message "``Segmentation fault (core dumped)``". What should I do?

   One possible solution is changing your Python to 3.6.2 (Intel Corporation).

   .. code-block:: bash

      conda install python=3.6.2 -c intel


* The CKIPWS throws "``what():  locale::facet::_S_create_c_locale name not valid``". What should I do?

   Please install locales-all.

   .. code-block:: console

      apt-get install locales-all
