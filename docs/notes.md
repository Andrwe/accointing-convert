# Random Notes


## Build within virtualenv

```
python -m pip install virtualenv
python -m virtualenv --copies /tmp/venv
/tmp/venv/bin/pip install -U pip
/tmp/venv/bin/pip install -r /app/requirements.txt
/tmp/venv/bin/pip install pyinstaller staticx patchelf
. /tmp/venv/bin/activate
curl -sLo - "https://github.com/upx/upx/releases/download/v3.96/upx-3.96-amd64_linux.tar.xz" | tar -C /tmp -xvJf - "upx-3.96-amd64_linux/upx"
/tmp/venv/bin/pyinstaller
/tmp/venv/bin/staticx
```

## Build with docker image python:3

```
apt update
apt install scons
python -m pip install virtualenv
python -m virtualenv --copies /tmp/venv
. /tmp/venv/bin/activate
/tmp/venv/bin/pip install -U pip
/tmp/venv/bin/pip install -r /app/requirements.txt
/tmp/venv/bin/pip install scons
/tmp/venv/bin/pip install --no-binary=staticx pyinstaller staticx patchelf
curl -sLo - "https://github.com/upx/upx/releases/download/v3.96/upx-3.96-amd64_linux.tar.xz" | tar -C /tmp -xvJf - "upx-3.96-amd64_linux/upx"
/tmp/venv/bin/pyinstaller
/tmp/venv/bin/staticx
```
