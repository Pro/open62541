git submodule update --init --recursive

if not exist "%CYG_ROOT%" mkdir "%CYG_ROOT%"

# Cygwin
echo "Installing Cygwin from $env:CYG_SETUP_URL to $env:CYG_ROOT/setup-x86.exe"
& appveyor DownloadFile %CYG_SETUP_URL% -FileName %CYG_ROOT%/setup-x86.exe
echo "Downloaded. Now ready to install."

& "$env:CYG_ROOT/setup-x86.exe" --quiet-mode --no-shortcuts --only-site -R "$env:CYG_ROOT" -s "$env:CYG_MIRROR" -l "$env:CYG_CACHE" --packages cmake,python'
& "$env:CYG_BASH" -lc "cygcheck -dc cygwin"'

# Install miktex to get pdflatex, if we don't get it from the cache
if (-not (Test-Path "c:\miktex\texmfs\install\miktex\bin\pdflatex.exe")) {
	& appveyor DownloadFile http://mirrors.ctan.org/systems/win32/miktex/setup/miktex-portable.exe
	& 7z x miktex-portable.exe -oc:\miktex >NUL

	# Remove some big files to reduce size to be cached
	Remove-Item -Path c:\miktex\texmfs\install\doc -Recurse
	Remove-Item -Path c:\miktex\texmfs\install\internal -Recurse
	Remove-Item -Path c:\miktex\texmfs\install\miktex\bin\biber.exe
	Remove-Item -Path c:\miktex\texmfs\install\miktex\bin\icudt58.dll
	Remove-Item -Path c:\miktex\texmfs\install\miktex\bin\a5toa4.exe
}

& pip install --user sphinx sphinx_rtd_theme
& cinst graphviz.portable

# Download and build libcheck
& appveyor DownloadFile https://github.com/Pro/check/releases/download/0.12.0_win/check.zip
& 7z x check.zip -oc:\ >NUL

# Install DrMemory
& cinst drmemory