@echo off
rem make_puffus.cmd - compile Puffus.exe into the project folder (needs only the .NET Framework of Windows)
setlocal
set CSC=%WINDIR%\Microsoft.NET\Framework64\v4.0.30319\csc.exe
if not exist "%CSC%" set CSC=%WINDIR%\Microsoft.NET\Framework\v4.0.30319\csc.exe
if not exist "%CSC%" ( echo csc.exe not found - the .NET Framework 4 is missing & goto end )
cd /d "%~dp0"
"%CSC%" /nologo /target:winexe /optimize+ /out:..\..\Puffus.exe /win32manifest:app.manifest ^
  /r:System.dll /r:System.Core.dll /r:System.Drawing.dll /r:System.Windows.Forms.dll /r:System.Management.dll Puffus.cs
if errorlevel 1 ( echo. & echo Puffus.exe was NOT made - see the errors above. & goto end )
echo.
echo Done: Puffus.exe is in the project folder:
for %%F in ("%~dp0..\..\Puffus.exe") do echo   %%~fF
echo Start it from there (it asks for Administrator).
:end
echo.
pause
