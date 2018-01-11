# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXBUILD     = sphinx-build
SPHINXBUILDOPTS =
SPHINXAPI       = sphinx-apidoc
SPHINXAPIENVS   = "SPHINX_APIDOC_OPTIONS=special-members"
SPHINXAPIOPTS   =

PROJ = EntityLinking

DOCDIR    = .
BUILDDIR  = _build
SOURCEDIR = ../styleme
APIDIR    = _api

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(DOCDIR)" "$(BUILDDIR)" $(SPHINXBUILDOPTS)

.PHONY: help Makefile api clean

api:
	@$(SPHINXAPI) -fMeT -o "$(APIDIR)"  "$(SOURCEDIR)" $(SPHINXAPIOPTS)

clean: Makefile
	@$(SPHINXBUILD) -M $@ "$(DOCDIR)" "$(BUILDDIR)" $(SPHINXBUILDOPTS)
	@$(SPHINXBUILD) -M $@ "$(DOCDIR)" "$(APIDIR)" $(SPHINXBUILDOPTS)

# Catch-all target: route all unknown targets to Sphinx using the new "make mode" option.
%: api Makefile
	@$(SPHINXBUILD) -M $@ "$(DOCDIR)" "$(BUILDDIR)" $(SPHINXBUILDOPTS)
