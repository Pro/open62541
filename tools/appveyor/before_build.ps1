$ErrorActionPreference = "Stop"

# use MinGW64
[Environment]::SetEnvironmentVariable("Path", "C:\mingw-w64\i686-5.3.0-posix-dwarf-rt_v4-rev0\mingw32\bin;" + $env:Path, [EnvironmentVariableTarget]::Machine)

# Workaround for CMake not wanting sh.exe on PATH for MinGW
[Environment]::SetEnvironmentVariable("Path", $env:Path.replace("C:\Program Files\Git\usr\bin;",""), [EnvironmentVariableTarget]::Machine)

# Miktex
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";c:\miktex\texmfs\install\miktex\bin", [EnvironmentVariableTarget]::Machine)
# We also need miktex for the following script
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";c:\miktex\texmfs\install\miktex\bin", [EnvironmentVariableTarget]::Process)
# autoinstall latex packages (0=no, 1=autoinstall, 2=ask)
# this adds this to the registry!
& initexmf --set-config-value [MPM]AutoInstall=1
& initexmf --update-fndb

# Python

[Environment]::SetEnvironmentVariable("Path", $env:Path + ";$env:APPDATA\Python\Scripts", [EnvironmentVariableTarget]::Machine)

# DrMemory
#[Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\Program Files (x86)\Dr. Memory\bin", [EnvironmentVariableTarget]::Machine)


echo "PATH=$env:PATH"