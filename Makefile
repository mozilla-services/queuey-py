APPNAME = queuey-py
DEPS =
HERE = $(shell pwd)
BIN = $(HERE)/bin
VIRTUALENV = virtualenv-2.6
NOSE = bin/nosetests -s --with-xunit
TESTS = $(APPNAME)/tests
PYTHON = $(HERE)/bin/python
BUILDAPP = $(HERE)/bin/buildapp
BUILDRPMS = $(HERE)/bin/buildrpms
PYPI = http://pypi.python.org/simple
PYPIOPTIONS = -i $(PYPI)
DOTCHANNEL := $(wildcard .channel)
ifeq ($(strip $(DOTCHANNEL)),)
	CHANNEL = dev
	RPM_CHANNEL = prod
else
	CHANNEL = `cat .channel`
	RPM_CHANNEL = `cat .channel`
endif
INSTALL = $(HERE)/bin/pip install
PIP_DOWNLOAD_CACHE ?= /tmp/pip_cache
INSTALLOPTIONS = --download-cache $(PIP_DOWNLOAD_CACHE) -U -i $(PYPI) \
	--use-mirrors
NGINX_VERSION = 1.2.1

ifdef PYPIEXTRAS
	PYPIOPTIONS += -e $(PYPIEXTRAS)
	INSTALLOPTIONS += -f $(PYPIEXTRAS)
endif

ifdef PYPISTRICT
	PYPIOPTIONS += -s
	ifdef PYPIEXTRAS
		HOST = `python2.6 -c "import urlparse; print urlparse.urlparse('$(PYPI)')[1] + ',' + urlparse.urlparse('$(PYPIEXTRAS)')[1]"`

	else
		HOST = `python2.6 -c "import urlparse; print urlparse.urlparse('$(PYPI)')[1]"`
	endif

endif

INSTALL += $(INSTALLOPTIONS)

SW = sw
NGINX = $(BIN)/nginx
BUILD_DIRS = bin build deps include lib lib64 man


.PHONY: all build test build_rpms mach
.SILENT: lib python pip $(NGINX) nginx

all: build

$(BIN)/python:
	python2.6 $(SW)/virtualenv.py --distribute . >/dev/null 2>&1
	rm distribute-0.6.*.tar.gz

$(BIN)/pip: $(BIN)/python

lib: $(BIN)/pip
	@echo "Installing package pre-requisites..."
	$(INSTALL) -r dev-reqs.txt

$(NGINX):
	@echo "Installing Nginx"
	mkdir -p bin
	cd bin && \
	curl --silent http://nginx.org/download/nginx-$(NGINX_VERSION).tar.gz | tar -zx
	mv bin/nginx-$(NGINX_VERSION) bin/nginx
	cd bin/nginx && \
	./configure --prefix=$(HERE)/bin/nginx --with-http_ssl_module \
	--conf-path=../../etc/nginx/nginx.conf --pid-path=../../var/nginx.pid \
	--lock-path=../../var/nginx.lock --error-log-path=../../var/log/nginx-error.log \
	--http-log-path=../../var/log/nginx-access.log >/dev/null 2>&1 && \
	make >/dev/null 2>&1 && make install >/dev/null 2>&1
	@echo "Finished installing Nginx"

nginx: $(NGINX)

clean-nginx:
	rm -rf bin/nginx

clean-env:
	rm -rf $(BUILD_DIRS)

clean: clean-env

build: lib nginx
	$(BUILDAPP) -c $(CHANNEL) $(PYPIOPTIONS) $(DEPS)

html:
	cd docs && make html

test:
	@echo "Running tests..."
	$(PYTHON) runtests.py
	@echo "Finished running tests"

test-python:
	$(NOSE) --with-coverage --cover-package=queuey_py \
	--cover-inclusive queuey_py \
	--set-env-variables="{'REQUESTS_CA_BUNDLE': '$(HERE)/etc/ssl/localhost.crt'}" \
	$(ARG)
