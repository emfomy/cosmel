# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXBUILD     = sphinx-build
SPHINXBUILDOPTS =
SPHINXAPI       = sphinx-apidoc
SPHINXAPIOPTS   =

PROJ = CosmEL

DOCDIR     = .
BUILDDIR   = _build
APIDIR     = _api

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(DOCDIR)" "$(BUILDDIR)" $(SPHINXBUILDOPTS)

.PHONY: help Makefile api clean

api:
	@$(SPHINXAPI) -feTM -o "$(APIDIR)" "../cosmel" $(SPHINXAPIOPTS)
	@perl -i -0pe 's/Subpackages\n-----------//g;s/Submodules\n----------//g' $(APIDIR)/*

clean: Makefile
	@$(SPHINXBUILD) -M $@ "$(DOCDIR)" "$(BUILDDIR)" $(SPHINXBUILDOPTS)
	@$(SPHINXBUILD) -M $@ "$(DOCDIR)" "$(APIDIR)"   $(SPHINXBUILDOPTS)

html: api Makefile
	@$(SPHINXBUILD) -M $@ "$(DOCDIR)" "$(BUILDDIR)" $(SPHINXBUILDOPTS)

latex: api Makefile
	@$(SPHINXBUILD) -M $@ "$(DOCDIR)" "$(BUILDDIR)" $(SPHINXBUILDOPTS)
	@$(SPHINXBUILD) -M latexpdf "$(DOCDIR)" "$(BUILDDIR)" $(SPHINXBUILDOPTS)

latexpdf: Makefile
	$(error "Use make latex instead!")

# Catch-all target: route all unknown targets to Sphinx using the new "make mode" option.
%: api Makefile
	@$(SPHINXBUILD) -M $@ "$(DOCDIR)" "$(BUILDDIR)" $(SPHINXBUILDOPTS)
