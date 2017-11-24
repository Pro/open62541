& git submodule --quiet update --init --recursive

#if (-not (Test-Path "$env:CYG_ROOT")) {
#	New-Item -ItemType directory -Path "$env:CYG_ROOT"
#}

# Cygwin
echo "`n### Installing Cygwin from $env:CYG_SETUP_URL to $env:CYG_ROOT/setup-x86.exe ###`n"
#& cinst --no-progress cygwin cyg-get
#& cinst cygwin -y --installargs "-DdgP cmake"
#& cinst cygwin -y --installargs "-DdgP python"
# & cyg-get cmake python
#& "$env:CYG_BASH" -lc "cygcheck -dc cygwin"'
#choco install cyg-get -y cmake python
echo "Installing Cygwin from $env:CYG_SETUP_URL to $env:CYG_ROOT/setup-x86.exe"
& appveyor DownloadFile "$env:CYG_SETUP_URL" -FileName "$env:CYG_ROOT/setup-x86.exe"
echo "Downloaded. Now ready to install."

& "$env:CYG_ROOT/setup-x86.exe" --quiet-mode --no-shortcuts --only-site -R "$env:CYG_ROOT" -s "$env:CYG_MIRROR" -l "$env:CYG_CACHE" --packages cmake,python'
& "$env:CYG_BASH" -lc "cygcheck -dc cygwin"'


echo "`n### Installing Miktex ###`n"
#if (-not (Test-Path "c:\miktex\texmfs\install\miktex\bin\pdflatex.exe")) {
#	& appveyor DownloadFile http://mirrors.ctan.org/systems/win32/miktex/setup/miktex-portable.exe
#	& 7z x miktex-portable.exe -oc:\miktex >NUL
#
#	# Remove some big files to reduce size to be cached
#	Remove-Item -Path c:\miktex\texmfs\install\doc -Recurse
#	Remove-Item -Path c:\miktex\texmfs\install\internal -Recurse
#	Remove-Item -Path c:\miktex\texmfs\install\miktex\bin\biber.exe
#	Remove-Item -Path c:\miktex\texmfs\install\miktex\bin\icudt58.dll
#	Remove-Item -Path c:\miktex\texmfs\install\miktex\bin\a5toa4.exe
#}
& cinst --no-progress miktex.portable

echo "`n### Installing sphinx ###`n"
& pip install --quiet --user sphinx sphinx_rtd_theme

echo "`n### Installing graphviz ###`n"
& cinst --no-progress graphviz.portable

echo "`n### Installing libcheck ###`n"
& appveyor DownloadFile https://github.com/Pro/check/releases/download/0.12.0_win/check.zip
& 7z x check.zip -oc:\ -bso0 -bsp0

echo "`n### Installing DrMemory ###`n"
& cinst --no-progress drmemory.portable