@echo off
setlocal

:: Get current date and time for commit message
set "datetime=%date% %time%"

echo ============================================
echo      PrismView Auto-Sync to GitHub
echo ============================================
echo.

:: Check if git is installed
where git >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: Git is not installed or not in PATH.
    pause
    exit /b 1
)

:: Pull latest changes first to avoid conflicts
echo [1/3] Pulling latest changes from GitHub...
git pull origin main
if %errorlevel% neq 0 (
    echo Warning: Pull failed or repository is empty. Continuing...
)
echo.

:: Add all changes
echo [2/3] Adding changes...
git add .
echo.

:: Commit changes
echo [3/3] Committing changes...
git commit -m "Auto-sync: %datetime%"
if %errorlevel% neq 0 (
    echo No changes to commit.
) else (
    echo Changes committed.
)
echo.

:: Push to GitHub
echo [4/4] Pushing to GitHub (origin main)...
git push -u origin main
if %errorlevel% neq 0 (
    echo.
    echo ============================================
    echo  ERROR: Push failed!
    echo  Possible reasons:
    echo   1. You haven't created the repository 'PrismView' on GitHub.
    echo   2. You don't have permission (login required).
    echo   3. Network issues.
    echo ============================================
    pause
    exit /b 1
)

echo.
echo ============================================
echo      Sync Complete! 
echo ============================================
timeout /t 3 >nul
