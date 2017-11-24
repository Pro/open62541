$ErrorActionPreference = "Stop"

cd c:\projects\open62541
# Collect files for .zip packing
New-Item -ItemType directory -Path "pack"
Copy-Item "$env:APPVEYOR_BUILD_FOLDER\LICENSE" pack\
Copy-Item "$env:APPVEYOR_BUILD_FOLDER\AUTHORS" pack\
Copy-Item ""$env:APPVEYOR_BUILD_FOLDER\README.md" pack\

echo "`n##### Building Documentation on %CC_NAME% #####`n"
New-Item -ItemType directory -Path "build"
cd build
cmake -DMIKTEX_BINARY_PATH=c:\miktex\texmfs\install\miktex\bin -DCMAKE_BUILD_TYPE=Release -DUA_COMPILE_AS_CXX:BOOL=%FORCE_CXX% -DUA_BUILD_EXAMPLES:BOOL=OFF -G"%CC_NAME%" ..
cmake --build . --target doc_latex
cmake --build . --target doc_pdf
move "%APPVEYOR_BUILD_FOLDER%\build\doc_latex\open62541.pdf" %APPVEYOR_BUILD_FOLDER%\pack\
cd ..
Remove-Item -Path c:\miktex\texmfs\install\doc -Recurse

echo "`n##### Testing %CC_NAME% #####`n"
New-Item -ItemType directory -Path "build"
cd build
cmake -DUA_BUILD_EXAMPLES:BOOL=ON -DUA_COMPILE_AS_CXX:BOOL=%FORCE_CXX% -G"%CC_NAME%" ..
'%MAKE%'
cd ..
Remove-Item -Path c:\miktex\texmfs\install\doc -Recurse

echo "`n##### Testing %CC_NAME% with full NS0 #####`n"
New-Item -ItemType directory -Path "build"
cd build
cmake -DUA_BUILD_EXAMPLES:BOOL=ON -DUA_ENABLE_FULL_NS0:BOOL=ON -DUA_COMPILE_AS_CXX:BOOL=%FORCE_CXX% -G"%CC_NAME%" ..
'%MAKE%'
cd ..
Remove-Item -Path c:\miktex\texmfs\install\doc -Recurse

echo "`n##### Testing %CC_NAME% with amalgamation #####`n"
New-Item -ItemType directory -Path "build"
cd build
cmake -DCMAKE_BUILD_TYPE=RelWithDebInfo -DUA_BUILD_EXAMPLES:BOOL=ON -DUA_ENABLE_AMALGAMATION:BOOL=ON -DUA_COMPILE_AS_CXX:BOOL=%FORCE_CXX% -DBUILD_SHARED_LIBS:BOOL=OFF -G"%CC_NAME%" ..
'%MAKE%'
md %APPVEYOR_BUILD_FOLDER%\pack_tmp
move "%APPVEYOR_BUILD_FOLDER%\build\open62541.c" %APPVEYOR_BUILD_FOLDER%\pack_tmp\
move "%APPVEYOR_BUILD_FOLDER%\build\open62541.h" %APPVEYOR_BUILD_FOLDER%\pack_tmp\
move "%APPVEYOR_BUILD_FOLDER%\build\%OUT_DIR_EXAMPLES%\server.exe" %APPVEYOR_BUILD_FOLDER%\pack_tmp\
move "%APPVEYOR_BUILD_FOLDER%\build\%OUT_DIR_EXAMPLES%\client.exe" %APPVEYOR_BUILD_FOLDER%\pack_tmp\
if "%CC_SHORTNAME%" == "mingw" move "%APPVEYOR_BUILD_FOLDER%\build\%OUT_DIR_LIB%\libopen62541.a" %APPVEYOR_BUILD_FOLDER%\pack_tmp\
if not "%CC_SHORTNAME%" == "mingw" move "%APPVEYOR_BUILD_FOLDER%\build\%OUT_DIR_LIB%\open62541.lib" %APPVEYOR_BUILD_FOLDER%\pack_tmp\
cd ..
7z a -tzip open62541-%CC_SHORTNAME%-static.zip "%APPVEYOR_BUILD_FOLDER%\pack\*" "%APPVEYOR_BUILD_FOLDER%\pack_tmp\*"
rd /s /q pack_tmp
Remove-Item -Path c:\miktex\texmfs\install\doc -Recurse

echo "`n##### Testing %CC_NAME% with amalgamation and .dll #####`n"
New-Item -ItemType directory -Path "build"
cd build
cmake -DCMAKE_BUILD_TYPE=RelWithDebInfo -DUA_BUILD_EXAMPLES:BOOL=ON -DUA_ENABLE_AMALGAMATION:BOOL=ON -DUA_COMPILE_AS_CXX:BOOL=%FORCE_CXX% -DBUILD_SHARED_LIBS:BOOL=ON -G"%CC_NAME%" ..
'%MAKE%'
md %APPVEYOR_BUILD_FOLDER%\pack_tmp
move "%APPVEYOR_BUILD_FOLDER%\build\open62541.c" %APPVEYOR_BUILD_FOLDER%\pack_tmp\
move "%APPVEYOR_BUILD_FOLDER%\build\open62541.h" %APPVEYOR_BUILD_FOLDER%\pack_tmp\
move "%APPVEYOR_BUILD_FOLDER%\build\%OUT_DIR_EXAMPLES%\server.exe" %APPVEYOR_BUILD_FOLDER%\pack_tmp\
move "%APPVEYOR_BUILD_FOLDER%\build\%OUT_DIR_EXAMPLES%\client.exe" %APPVEYOR_BUILD_FOLDER%\pack_tmp\
if "%CC_SHORTNAME%" == "mingw" move "%APPVEYOR_BUILD_FOLDER%\build\%OUT_DIR_LIB%\libopen62541.dll" %APPVEYOR_BUILD_FOLDER%\pack_tmp\
if "%CC_SHORTNAME%" == "mingw" move "%APPVEYOR_BUILD_FOLDER%\build\%OUT_DIR_LIB%\libopen62541.dll.a" %APPVEYOR_BUILD_FOLDER%\pack_tmp\
if not "%CC_SHORTNAME%" == "mingw" move "%APPVEYOR_BUILD_FOLDER%\build\%OUT_DIR_LIB%\open62541.dll" %APPVEYOR_BUILD_FOLDER%\pack_tmp\
if not "%CC_SHORTNAME%" == "mingw" move "%APPVEYOR_BUILD_FOLDER%\build\%OUT_DIR_LIB%\open62541.pdb" %APPVEYOR_BUILD_FOLDER%\pack_tmp\
cd ..
7z a -tzip open62541-%CC_SHORTNAME%-dynamic.zip "%APPVEYOR_BUILD_FOLDER%\pack\*" "%APPVEYOR_BUILD_FOLDER%\pack_tmp\*"
rd /s /q pack_tmp
Remove-Item -Path c:\miktex\texmfs\install\doc -Recurse

# Only execute unit tests on vs2015 to save compilation time
if "%CC_SHORTNAME%" == "vs2015" New-Item -ItemType directory -Path "build"
if "%CC_SHORTNAME%" == "vs2015" cd build
if "%CC_SHORTNAME%" == "vs2015" echo "`n##### Testing %CC_NAME% with unit tests #####`n"
if "%CC_SHORTNAME%" == "vs2015" cmake -DCMAKE_BUILD_TYPE=Debug -DUA_BUILD_EXAMPLES=OFF -DUA_ENABLE_DISCOVERY=ON -DUA_ENABLE_DISCOVERY_MULTICAST=ON -DUA_BUILD_UNIT_TESTS=ON -DUA_ENABLE_UNIT_TESTS_MEMCHECK=ON  -DCMAKE_LIBRARY_PATH=c:\check\lib -DCMAKE_INCLUDE_PATH=c:\check\include -DUA_COMPILE_AS_CXX:BOOL=%FORCE_CXX% -G"%CC_NAME%" ..
if "%CC_SHORTNAME%" == "vs2015" %MAKE%
if "%CC_SHORTNAME%" == "vs2015" cmake --build . --target test-verbose --config debug
# do not cache log
rd /s /q c:\miktex\texmfs\data\miktex\log