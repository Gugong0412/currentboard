@echo off
chcp 65001 > nul
cd /d "%~dp0"

rem ================================================================
rem  DDI 넷리스트 대조 실행기
rem  - 이 파일, kicad_netcheck.py, ddi_contract.json, board.net 을
rem    같은 폴더에 두고 더블클릭하세요.
rem  - .net 파일을 이 아이콘 위로 끌어다 놓아도 됩니다.
rem  - 완성본 전체 검사를 하려면 아래 MODE 줄을 set MODE= 로 바꾸세요.
rem ================================================================
set MODE=--partial

set NET=%~1
if "%NET%"=="" set NET=board.net

if not exist "%NET%" (
  echo [중단] 넷리스트 파일 "%NET%" 이 없습니다.
  echo        KiCad에서 board.net 으로 내보내거나, .net 파일을 이 아이콘에 끌어다 놓으세요.
  pause
  exit /b 1
)

set PY=
where py > nul 2>&1 && set PY=py
if "%PY%"=="" where python > nul 2>&1 && set PY=python
if "%PY%"=="" (
  echo [중단] Python을 찾지 못했습니다. python.org 에서 설치하세요.
  echo        설치 화면에서 "Add python.exe to PATH" 를 꼭 체크하세요.
  pause
  exit /b 1
)

%PY% kicad_netcheck.py ddi_contract.json "%NET%" %MODE% --csv report.csv
echo.
echo 결과는 report.csv 에도 저장되었습니다 (엑셀로 열기).
pause
