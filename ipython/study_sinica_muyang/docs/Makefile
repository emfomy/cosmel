# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXBUILD     = sphinx-build
SPHINXBUILDOPTS =
SPHINXAPI       = sphinx-apidoc
SPHINXAPIENVS   = "SPHINX_APIDOC_OPTIONS=special-members"
SPHINXAPIOPTS   =

PROJ = StyleMe

DOCDIR     = .
BUILDDIR   = _build
SOURCEDIR1 = ../styleme
SOURCEDIR2 = ../model
APIDIR     = _api

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(DOCDIR)" "$(BUILDDIR)" $(SPHINXBUILDOPTS)

.PHONY: help Makefile api clean

api:
	@$(SPHINXAPI) -fMeT -o "$(APIDIR)" "$(SOURCEDIR1)" $(SPHINXAPIOPTS)
	@$(SPHINXAPI) -fMeT -o "$(APIDIR)" "$(SOURCEDIR2)" $(SPHINXAPIOPTS)

clean: Makefile
	@$(SPHINXBUILD) -M $@ "$(DOCDIR)" "$(BUILDDIR)" $(SPHINXBUILDOPTS)
	@$(SPHINXBUILD) -M $@ "$(DOCDIR)" "$(APIDIR)" $(SPHINXBUILDOPTS)

# Catch-all target: route all unknown targets to Sphinx using the new "make mode" option.
%: api Makefile
	@$(SPHINXBUILD) -M $@ "$(DOCDIR)" "$(BUILDDIR)" $(SPHINXBUILDOPTS)
