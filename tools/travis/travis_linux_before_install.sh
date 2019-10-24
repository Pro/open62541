#!/bin/bash
set -e

if [ -z ${LOCAL_PKG+x} ] || [ -z "$LOCAL_PKG" ]; then
    echo "LOCAL_PKG is not set. Aborting..."
    exit 1
fi

if ! [ -z ${CLANG_FORMAT+x} ]; then
    echo "CLANG_FORMAT does not need any dependencies. Done."
    exit 0
fi

if [ "$ARCH" = "freertoslwip" ]; then
    echo -e "\r\n==FREERTOS BUILD==" && echo -en 'travis_fold:start:before_install.build.freertos\\r'
	git clone -b v3.2.3 --recursive https://github.com/espressif/esp-idf.git $IDF_PATH
	cd $IDF_PATH
	python -m pip install --user -r $IDF_PATH/requirements.txt
	cd $HOME/esp
	wget https://dl.espressif.com/dl/xtensa-esp32-elf-linux64-1.22.0-80-g6c4433a-5.2.0.tar.gz
	tar -xf xtensa-esp32-elf-linux64-1.22.0-80-g6c4433a-5.2.0.tar.gz -C $LOCAL_PKG
    echo -en 'travis_fold:end:before_install.build.freertos\\r'
	exit 0
fi


if [ -z ${DOCKER+x} ] && [ -z ${SONAR+x} ] &&  [ -z ${ARCH} ]; then
	# Only on non-docker builds required

 	echo "=== Installing from external package sources in $LOCAL_PKG ===" && echo -en 'travis_fold:start:before_install.external\\r'

   # Increase the environment version to force a rebuild of the packages
    # The version is writen to the cache file after every build of the dependencies
    ENV_VERSION="1"
    ENV_INSTALLED=""
    if [ -e $LOCAL_PKG/.build_env ]; then
        echo "=== No cached build environment ==="
        read -r ENV_INSTALLED < $LOCAL_PKG/.build_env
    fi

    # travis caches the $LOCAL_PKG dir. If it is loaded, we don't need to reinstall the packages
    if [ "$ENV_VERSION" = "$ENV_INSTALLED" ]; then
        echo "=== The build environment is current ==="
        exit 0
    fi

    echo "=== The build environment is outdated ==="

    # Clean up
    # additional safety measure to avoid rm -rf on root
    # only execute it on travis
    if ! [ -z ${TRAVIS+x} ]; then
        echo "rm -rf $LOCAL_PKG/*"
    fi

	if [ "$CC" = "tcc" ]; then
		mkdir tcc_install && cd tcc_install
		wget https://mirror.netcologne.de/savannah/tinycc/tcc-0.9.27.tar.bz2
		tar xf tcc-0.9.27.tar.bz2
		cd tcc-0.9.27
		./configure --prefix=$LOCAL_PKG
		make
		make install
		cd ../..
		rm -rf tcc_install
	fi

	wget https://github.com/ARMmbed/mbedtls/archive/mbedtls-2.7.1.tar.gz
	tar xf mbedtls-2.7.1.tar.gz
	cd mbedtls-mbedtls-2.7.1
	cmake -DENABLE_TESTING=Off -DCMAKE_INSTALL_PREFIX=$LOCAL_PKG .
	make -j
	make install

	echo -en 'travis_fold:end:script.before_install.external\\r'

	echo "=== Installing python packages ===" && echo -en 'travis_fold:start:before_install.python\\r'
	pip install --user cpp-coveralls
	# Pin docutils to version smaller 0.15. Otherwise we run into https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=839299
	pip install --user 'docutils<=0.14'
	pip install --user sphinx_rtd_theme
	pip install --user cpplint
	echo -en 'travis_fold:end:script.before_install.python\\r'

fi
