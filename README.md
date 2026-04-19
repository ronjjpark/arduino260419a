# Python Arduino GUI Controller

Python GUI로 아두이노를 제어하는 예제 프로그램입니다.

`tkinter` 기반 그래픽 화면에서 시리얼 포트를 연결하고 LED, PWM 출력, 서보모터를 제어할 수 있습니다.

## 구성 파일

- `arduino_gui_controller.py`: Python GUI 프로그램
- `arduino_serial_controller.ino`: 아두이노에 업로드할 예제 스케치
- `requirements.txt`: Python 의존성
- `install_and_run.bat`: 설치 후 바로 실행하는 Windows 배치 파일
- `run.bat`: 이미 설치가 끝난 뒤 빠르게 실행하는 Windows 배치 파일

## 가장 쉬운 실행 방법

Windows에서 `install_and_run.bat` 파일을 더블클릭하세요.

이 파일은 아래 작업을 자동으로 처리합니다.

1. `.venv` 가상환경 생성
2. `pyserial` 설치
3. Python GUI 프로그램 실행

PowerShell에서 실행하려면 다음 명령을 사용하세요.

```powershell
.\install_and_run.bat
```

## 직접 설치하고 실행하기

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python arduino_gui_controller.py
```

이미 설치가 끝났다면 다음 중 하나로 실행할 수 있습니다.

```powershell
.\run.bat
```

또는

```powershell
.\.venv\Scripts\python.exe arduino_gui_controller.py
```

## 아두이노 준비

1. Arduino IDE를 실행합니다.
2. `arduino_serial_controller.ino` 파일 내용을 새 스케치에 붙여넣습니다.
3. 보드와 포트를 선택합니다.
4. 업로드합니다.
5. Arduino IDE의 시리얼 모니터는 닫아둡니다. 같은 포트를 Python과 동시에 사용할 수 없습니다.

## 사용 방법

1. Python 프로그램을 실행합니다.
2. `Refresh`를 눌러 COM 포트를 갱신합니다.
3. 아두이노 포트를 선택합니다.
4. Baud rate는 아두이노 코드와 동일하게 `9600`으로 둡니다.
5. `Connect`를 누릅니다.
6. LED, PWM, Servo 제어 버튼과 슬라이더를 사용합니다.

## 명령 프로토콜

Python 프로그램은 아두이노로 아래 형식의 텍스트 명령을 보냅니다.

```text
D pin value     예: D 13 1      디지털 출력 HIGH
D pin value     예: D 13 0      디지털 출력 LOW
P pin value     예: P 9 128     PWM 출력 0-255
S pin angle     예: S 10 90     서보 각도 0-180
R pin           예: R 2         디지털 입력 읽기
```

## 기본 연결 예

- LED: 디지털 13번 핀 또는 저항을 연결한 외부 LED
- PWM LED 밝기: PWM 지원 핀 3, 5, 6, 9, 10, 11 중 하나
- 서보모터: 신호선 10번 핀, 전원 5V, GND 연결

서보모터는 전류를 많이 사용합니다. USB 전원만으로 불안정하면 별도 5V 전원을 사용하고 GND를 아두이노와 공통으로 연결하세요.

## 실행이 안 될 때

### 1. `pyserial` 오류가 나는 경우

아래 명령으로 설치하세요.

```powershell
pip install -r requirements.txt
```

가상환경을 사용하는 경우에는 다음 명령을 사용하세요.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2. COM 포트가 보이지 않는 경우

- 아두이노 USB 케이블을 다시 연결합니다.
- Arduino IDE에서 보드와 포트가 잡히는지 확인합니다.
- CH340 계열 호환 보드는 드라이버 설치가 필요할 수 있습니다.
- `Refresh` 버튼을 다시 누릅니다.

### 3. 연결이 실패하는 경우

- Arduino IDE의 시리얼 모니터를 닫습니다.
- 다른 프로그램이 같은 COM 포트를 사용 중인지 확인합니다.
- Baud rate가 `9600`인지 확인합니다.
- 아두이노에 `arduino_serial_controller.ino`가 업로드되어 있는지 확인합니다.

### 4. PowerShell 실행 정책 오류가 나는 경우

가상환경 활성화가 막히면 활성화하지 않고 아래처럼 실행해도 됩니다.

```powershell
.\.venv\Scripts\python.exe arduino_gui_controller.py
```

또는 `install_and_run.bat`를 더블클릭하세요.

## 보완 제안

1. 센서값 그래프: 온도, 조도, 거리 센서 값을 실시간 그래프로 표시할 수 있습니다.
2. 자동 포트 탐지: 보드 이름이 포함된 포트를 우선 선택하도록 개선할 수 있습니다.
3. 장치별 프로파일: LED, 모터, 릴레이 등 장치 구성을 JSON 파일로 저장하고 불러올 수 있습니다.
4. 안전 기능: 릴레이나 모터 제어 시 종료할 때 모든 출력을 OFF로 만드는 비상 정지 버튼을 추가하는 것이 좋습니다.
5. 통신 안정성: 명령마다 ID를 붙여 응답 확인, 재전송, 타임아웃 처리를 넣으면 실험 장비 제어에 더 적합합니다.
6. 배포: 사용자가 Python을 몰라도 실행할 수 있게 PyInstaller로 `.exe` 파일을 만들 수 있습니다.
