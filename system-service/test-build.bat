@echo off
echo Testing Aera System Service Build...
echo.

dotnet build --configuration Release
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Build successful! 
    echo Generated files:
    dir bin\Release\net6.0-windows\AeraSystemService.*
    echo.
    echo Running integration tests...
    dotnet bin\Release\net6.0-windows\AeraSystemService.dll --integration-test
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo ❌ Integration tests failed!
        exit /b 1
    )
    echo ✅ Integration tests passed!
    echo.
    echo To install and run as Windows Service:
    echo sc create "AeraSystemService" binPath="[PATH_TO_EXE]"
    echo sc start AeraSystemService
) else (
    echo.
    echo ❌ Build failed!
    exit /b 1
)