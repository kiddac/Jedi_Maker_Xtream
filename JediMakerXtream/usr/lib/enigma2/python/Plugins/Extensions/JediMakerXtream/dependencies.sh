#!/bin/sh
pyv="$(python -V 2>&1)"
echo "$pyv"
echo "Checking Dependencies"
echo ""
echo "updating feeds"
if [ -d /etc/opkg ]; then

    opkg update
    echo ""
    if [[ $pyv =~ "Python 3" ]]; then
        echo "checking python3-requests"
        if python -c "import requests" &> /dev/null; then
            echo "Requests library already installed"
        else
            opkg install python3-requests
        fi
        echo ""

        echo "checking python3-multiprocessing"
        if python -c "from multiprocessing.pool import ThreadPool" &> /dev/null; then
            echo "Multiprocessing library already installed"
        else
            opkg install python3-multiprocessing
        fi
        echo ""

        echo "checking python3-lzma"
        if python -c "import lzma" &> /dev/null; then
            echo "lzma library already installed"
        else
            opkg install liblzma5
        fi
        echo ""
    else
        echo "checking python-requests"
        if python -c "import requests" &> /dev/null; then
            echo "Requests library already installed"
        else
            opkg install python-requests
        fi
        echo ""

        echo "checking python-multiprocessing"
        if python -c "from multiprocessing.pool import ThreadPool" &> /dev/null; then
            echo "Multiprocessing library already installed"
        else
            opkg install python-multiprocessing
        fi
        echo ""

        echo "checking python2-lzma"
        if python -c "import lzma" &> /dev/null; then
            echo "lzma library already installed"
        else
            opkg install python-lzma
        fi
        echo ""
    fi
else
    apt-get update
    echo ""
    if [[ $pyv =~ "Python 3" ]]; then
        echo "checking python3-requests"
        if python -c "import requests" &> /dev/null; then
            echo "Requests library already installed"
        else
            apt-get -y install python3-requests
        fi
        echo ""

        echo "checking python3-multiprocessing"
        if python -c "from multiprocessing.pool import ThreadPool" &> /dev/null; then
            echo "Multiprocessing library already installed"
        else
            apt-get -y install python3-multiprocessing
        fi
        echo ""

        echo "checking python3-lzma"
        if python -c "import lzma" &> /dev/null; then
            echo "lzma library already installed"
        else
            apt-get -y install liblzma5
        fi
        echo ""

    else
        echo "checking python-requests"
        if python -c "import requests" &> /dev/null; then
            echo "Requests library already installed"
        else
            apt-get -y install python-requests
        fi
        echo ""

        echo "checking python-multiprocessing"
        if python -c "from multiprocessing.pool import ThreadPool" &> /dev/null; then
            echo "Multiprocessing library already installed"
        else
            apt-get -y install python-multiprocessing
        fi
        echo ""

        echo "checking python2-lzma"
        if python -c "import lzma" &> /dev/null; then
            echo "lzma library already installed"
        else
            apt-get -y install python-lzma
        fi
        echo ""
    fi
fi
exit 0
