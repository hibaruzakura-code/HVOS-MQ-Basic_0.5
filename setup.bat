@echo off
chcp 65001
echo ==========================================
echo  HVOS (MetaQuest版) に必要な部品を自動でインストールします
echo ==========================================

:: ① 通常の pip を試す
pip --version >nul 2>&1
if %errorlevel% == 0 (
    pip install flask pyautogui keyboard pygetwindow pillow google-genai
    goto SUCCESS
)

:: ② python -m pip を試す（PATH未反映対策）
python -m pip --version >nul 2>&1
if %errorlevel% == 0 (
    python -m pip install flask pyautogui keyboard pygetwindow pillow google-genai
    goto SUCCESS
)

:: ③ py -m pip を試す（Windows標準ランチャー）
py -m pip --version >nul 2>&1
if %errorlevel% == 0 (
    py -m pip install flask pyautogui keyboard pygetwindow pillow google-genai
    goto SUCCESS
)

:ERROR
echo.
echo 【エラー】Python または pip が見つかりませんでした。
echo.
echo ■ 対策：
echo 1. パソコンを一度「再起動」してから、もう一度このファイルをダブルクリックしてください。
echo 2. それでもダメな場合は、Pythonのインストール時に「Add python.exe to PATH」に
echo    チェックを入れたか確認し、Pythonを再インストールしてください。
echo.
pause
exit

:SUCCESS
echo.
echo ------------------------------------------
echo 準備が完了しました！この画面は閉じて大丈夫です。
echo ------------------------------------------
pause