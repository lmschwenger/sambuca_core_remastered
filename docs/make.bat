@ECHO OFF

pushd %~dp0

REM Command file for Sphinx documentation

if "%SPHINXBUILD%" == "" (
	set SPHINXBUILD=sphinx-build
)
set SOURCEDIR=source
set BUILDDIR=build

if "%1" == "" goto help

%SPHINXBUILD% >NUL 2>NUL
if errorlevel 9009 (
	echo.
	echo.The 'sphinx-build' command was not found. Make sure you have Sphinx
	echo.installed, then set the SPHINXBUILD environment variable to point
	echo.to the full path of the 'sphinx-build' executable. Alternatively you
	echo.may add the Sphinx directory to PATH.
	echo.
	echo.If you don't have Sphinx installed, grab it from
	echo.https://sphinx-doc.org/
	exit /b 1
)

%SPHINXBUILD% -M %1 %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%
goto end

:help
%SPHINXBUILD% -M help %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%

:end
popd

REM Custom targets for SAMBUCA documentation

if "%1" == "clean" (
	echo.Cleaning build directory...
	rmdir /s /q %BUILDDIR% 2>NUL
	mkdir %BUILDDIR%
	echo.Build directory cleaned.
	goto end
)

if "%1" == "docs" (
	echo.Building HTML documentation...
	%SPHINXBUILD% -M html %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%
	echo.Documentation built successfully!
	echo.Open %BUILDDIR%\html\index.html in your browser
	goto end
)

if "%1" == "pdf" (
	echo.Building PDF documentation...
	%SPHINXBUILD% -M latexpdf %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%
	goto end
)

if "%1" == "linkcheck" (
	echo.Checking links...
	%SPHINXBUILD% -M linkcheck %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%
	goto end
)
