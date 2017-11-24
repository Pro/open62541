$ErrorActionPreference = "Stop"

cd c:\projects\open62541
# Collect files for .zip packing
New-Item -ItemType directory -Path "pack"
Copy-Item "$env:APPVEYOR_BUILD_FOLDER\LICENSE" pack\
Copy-Item "$env:APPVEYOR_BUILD_FOLDER\AUTHORS" pack\
Copy-Item ""$env:APPVEYOR_BUILD_FOLDER\README.md" pack\

echo "`n##### Building Documentation on $env:CC_NAME #####`n"
New-Item -ItemType directory -Path "build"
cd build
cmake -DMIKTEX_BINARY_PATH=c:\miktex\texmfs\install\miktex\bin -DCMAKE_BUILD_TYPE=Release -DUA_COMPILE_AS_CXX:BOOL=$env:FORCE_CXX -DUA_BUILD_EXAMPLES:BOOL=OFF -G"$env:CC_NAME" ..
cmake --build . --target doc_latex
cmake --build . --target doc_pdf
move "$env:APPVEYOR_BUILD_FOLDER\build\doc_latex\open62541.pdf" $env:APPVEYOR_BUILD_FOLDER\pack\
cd ..
Remove-Item -Path build -Recurse

echo "`n##### Testing $env:CC_NAME #####`n"
New-Item -ItemType directory -Path "build"
cd build
cmake -DUA_BUILD_EXAMPLES:BOOL=ON -DUA_COMPILE_AS_CXX:BOOL=$env:FORCE_CXX -G"$env:CC_NAME" ..
$env:MAKE
cd ..
Remove-Item -Path build -Recurse

echo "`n##### Testing $env:CC_NAME with full NS0 #####`n"
New-Item -ItemType directory -Path "build"
cd build
cmake -DUA_BUILD_EXAMPLES:BOOL=ON -DUA_ENABLE_FULL_NS0:BOOL=ON -DUA_COMPILE_AS_CXX:BOOL=$env:FORCE_CXX -G"$env:CC_NAME" ..
$env:MAKE
cd ..
Remove-Item -Path build -Recurse

echo "`n##### Testing $env:CC_NAME with amalgamation #####`n"
New-Item -ItemType directory -Path "build"
cd build
cmake -DCMAKE_BUILD_TYPE=RelWithDebInfo -DUA_BUILD_EXAMPLES:BOOL=ON -DUA_ENABLE_AMALGAMATION:BOOL=ON -DUA_COMPILE_AS_CXX:BOOL=$env:FORCE_CXX -DBUILD_SHARED_LIBS:BOOL=OFF -G"$env:CC_NAME" ..
$env:MAKE
md $env:APPVEYOR_BUILD_FOLDER\pack_tmp
move "$env:APPVEYOR_BUILD_FOLDER\build\open62541.c" $env:APPVEYOR_BUILD_FOLDER\pack_tmp\
move "$env:APPVEYOR_BUILD_FOLDER\build\open62541.h" $env:APPVEYOR_BUILD_FOLDER\pack_tmp\
move "$env:APPVEYOR_BUILD_FOLDER\build\$env:OUT_DIR_EXAMPLES\server.exe" $env:APPVEYOR_BUILD_FOLDER\pack_tmp\
move "$env:APPVEYOR_BUILD_FOLDER\build\$env:OUT_DIR_EXAMPLES\client.exe" $env:APPVEYOR_BUILD_FOLDER\pack_tmp\
if ($env:CC_SHORTNAME -eq "mingw") {
	move "$env:APPVEYOR_BUILD_FOLDER\build\$env:OUT_DIR_LIB\libopen62541.a" $env:APPVEYOR_BUILD_FOLDER\pack_tmp\
	move "$env:APPVEYOR_BUILD_FOLDER\build\$env:OUT_DIR_LIB\open62541.lib" $env:APPVEYOR_BUILD_FOLDER\pack_tmp\
}
cd ..
7z a -tzip open62541-$env:CC_SHORTNAME-static.zip "$env:APPVEYOR_BUILD_FOLDER\pack\*" "$env:APPVEYOR_BUILD_FOLDER\pack_tmp\*"
Remove-Item -Path pack_tmp -Recurse
Remove-Item -Path build -Recurse

echo "`n##### Testing $env:CC_NAME with amalgamation and .dll #####`n"
New-Item -ItemType directory -Path "build"
cd build
cmake -DCMAKE_BUILD_TYPE=RelWithDebInfo -DUA_BUILD_EXAMPLES:BOOL=ON -DUA_ENABLE_AMALGAMATION:BOOL=ON -DUA_COMPILE_AS_CXX:BOOL=$env:FORCE_CXX -DBUILD_SHARED_LIBS:BOOL=ON -G"$env:CC_NAME" ..
$env:MAKE
md $env:APPVEYOR_BUILD_FOLDER\pack_tmp
move "$env:APPVEYOR_BUILD_FOLDER\build\open62541.c" $env:APPVEYOR_BUILD_FOLDER\pack_tmp\
move "$env:APPVEYOR_BUILD_FOLDER\build\open62541.h" $env:APPVEYOR_BUILD_FOLDER\pack_tmp\
move "$env:APPVEYOR_BUILD_FOLDER\build\$env:OUT_DIR_EXAMPLES\server.exe" $env:APPVEYOR_BUILD_FOLDER\pack_tmp\
move "$env:APPVEYOR_BUILD_FOLDER\build\$env:OUT_DIR_EXAMPLES\client.exe" $env:APPVEYOR_BUILD_FOLDER\pack_tmp\
if ($env:CC_SHORTNAME -eq "mingw") {
	move "$env:APPVEYOR_BUILD_FOLDER\build\$env:OUT_DIR_LIB\libopen62541.dll" $env:APPVEYOR_BUILD_FOLDER\pack_tmp\
	move "$env:APPVEYOR_BUILD_FOLDER\build\$env:OUT_DIR_LIB\libopen62541.dll.a" $env:APPVEYOR_BUILD_FOLDER\pack_tmp\
} else {
	move "$env:APPVEYOR_BUILD_FOLDER\build\$env:OUT_DIR_LIB\open62541.dll" $env:APPVEYOR_BUILD_FOLDER\pack_tmp\
	move "$env:APPVEYOR_BUILD_FOLDER\build\$env:OUT_DIR_LIB\open62541.pdb" $env:APPVEYOR_BUILD_FOLDER\pack_tmp\
}
cd ..
7z a -tzip open62541-$env:CC_SHORTNAME-dynamic.zip "$env:APPVEYOR_BUILD_FOLDER\pack\*" "$env:APPVEYOR_BUILD_FOLDER\pack_tmp\*"
Remove-Item -Path pack_tmp -Recurse
Remove-Item -Path build -Recurse

if ($env:CC_SHORTNAME -eq "vs2015") {
	# Only execute unit tests on vs2015 to save compilation time
	New-Item -ItemType directory -Path "build"
	cd build
	echo "`n##### Testing $env:CC_NAME with unit tests #####`n"
	cmake -DCMAKE_BUILD_TYPE=Debug -DUA_BUILD_EXAMPLES=OFF -DUA_ENABLE_DISCOVERY=ON -DUA_ENABLE_DISCOVERY_MULTICAST=ON -DUA_BUILD_UNIT_TESTS=ON -DUA_ENABLE_UNIT_TESTS_MEMCHECK=ON  -DCMAKE_LIBRARY_PATH=c:\check\lib -DCMAKE_INCLUDE_PATH=c:\check\include -DUA_COMPILE_AS_CXX:BOOL=$env:FORCE_CXX -G"$env:CC_NAME" ..
	$env:MAKE
	cmake --build . --target test-verbose --config debug
}


# do not cache log
Remove-Item -Path c:\miktex\texmfs\data\miktex\log -Recurse