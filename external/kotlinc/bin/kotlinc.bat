@echo off
rem based on scalac.bat from the Scala distribution
rem ##########################################################################
rem # Copyright 2002-2011, LAMP/EPFL
rem # Copyright 2011-2015, JetBrains
rem #
rem # This is free software; see the distribution for copying conditions.
rem # There is NO warranty; not even for MERCHANTABILITY or FITNESS FOR A
rem # PARTICULAR PURPOSE.
rem ##########################################################################

rem We adopt the following conventions:
rem - System/user environment variables start with a letter
rem - Local batch variables start with an underscore ('_')

setlocal
call :set_home

if "%_KOTLIN_COMPILER%"=="" set _KOTLIN_COMPILER=org.jetbrains.kotlin.cli.jvm.K2JVMCompiler 

if not "%JAVA_HOME%"=="" (
  if exist "%JAVA_HOME%\bin\java.exe" set "_JAVACMD=%JAVA_HOME%\bin\java.exe"
)

if "%_JAVACMD%"=="" set _JAVACMD=java

rem We use the value of the JAVA_OPTS environment variable if defined
if "%JAVA_OPTS%"=="" set JAVA_OPTS=-Xmx256M -Xms32M

rem Iterate through arguments and split them into java and kotlin ones
:loop
set _arg=%~1
if "%_arg%" == "" goto loopend

if "%_arg:~0,2%"=="-J" (
  set JAVA_OPTS=%JAVA_OPTS% "%_arg:~2%"
) else (
  if "%_arg:~0,2%"=="-D" (
    set JAVA_OPTS=%JAVA_OPTS% "%_arg%"
  ) else (
    set KOTLIN_OPTS=%KOTLIN_OPTS% "%_arg%"
  )
)
shift
goto loop
:loopend

if "%_KOTLIN_RUNNER%"=="1" (
  "%_JAVACMD%" %JAVA_OPTS% "-Dkotlin.home=%_KOTLIN_HOME%" -cp "%_KOTLIN_HOME%\lib\kotlin-runner.jar" ^
    org.jetbrains.kotlin.runner.Main %KOTLIN_OPTS%
) else (
  setlocal EnableDelayedExpansion
  SET _ADDITIONAL_CLASSPATH=

  if not "%_KOTLIN_TOOL%"=="" (
    set _ADDITIONAL_CLASSPATH=;%_KOTLIN_HOME%\lib\%_KOTLIN_TOOL%
  )

  "%_JAVACMD%" %JAVA_OPTS% -noverify -cp "%_KOTLIN_HOME%\lib\kotlin-preloader.jar" ^
    org.jetbrains.kotlin.preloading.Preloader -cp "%_KOTLIN_HOME%\lib\kotlin-compiler.jar!_ADDITIONAL_CLASSPATH!" ^
    %_KOTLIN_COMPILER% %KOTLIN_OPTS%
)

exit /b %ERRORLEVEL%
goto end

rem ##########################################################################
rem # subroutines

:set_home
  set _BIN_DIR=
  for %%i in (%~sf0) do set _BIN_DIR=%_BIN_DIR%%%~dpsi
  set _KOTLIN_HOME=%_BIN_DIR%..
goto :eof

:end
endlocal

