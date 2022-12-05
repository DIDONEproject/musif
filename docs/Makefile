# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SPHINXAPIDOC	?= sphinx-apidoc
SOURCEDIR     = source
APIDOC 				= API
BUILDDIR      = build
APISRC 				= ../musif

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
clean:
	rm -r $(BUILDDIR)
	rm -r $(SOURCEDIR)/$(APIDOC)
	
%: Makefile
	export SPHINX_APIDOC_OPTIONS="members"
	@$(SPHINXAPIDOC) -e -o "$(SOURCEDIR)/$(APIDOC)" "$(APISRC)" 
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O) -v
