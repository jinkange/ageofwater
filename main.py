try:
    import cv2
    import numpy as np
    import pygetwindow as gw
    import pyautogui
    import keyboard
    import time
    import threading

    # 설정값
    target_title = "Age of Water"  # 예: "게임" 또는 "Unity Editor"
    threshold = 0.60  # 템플릿 매칭 임계값
    # 기준 해상도 (anchor.png가 캡처된 화면의 크기)
    REFERENCE_WIDTH = 1920
    REFERENCE_HEIGHT = 1080
    def detect_anchor_scaled_to_window(region):
        x, y, w, h = region
    
        # 1. 현재 창 크기 비율 계산
        scale_w = w / REFERENCE_WIDTH
        scale_h = h / REFERENCE_HEIGHT
        scale = (scale_w + scale_h) / 2  # 평균 비율 사용 (비율 깨질 경우 대비)
    
        # 2. 템플릿을 현재 창 비율에 맞게 리사이즈
        scaled_template = cv2.resize(template_gray, (0, 0), fx=scale, fy=scale)
    
        # 3. 스크린샷 캡처
        screenshot = pyautogui.screenshot(region=(x, y, w, h))
        screenshot_np = np.array(screenshot)
        screenshot_gray = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2GRAY)
    
        # 4. 템플릿 매칭 수행
        result = cv2.matchTemplate(screenshot_gray, scaled_template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)
        return max_val >= threshold
    
    # 닻 이미지 로드
    template = cv2.imread('./anchor.png', cv2.IMREAD_UNCHANGED)
    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    w, h = template_gray.shape[::-1]
    
    # 상태 변수
    detection_enabled = False
    running = True
except Exception as e:
    print(f"\n❌ 오류 발생: {e}")
    input("\n🔚 프로그램을 종료하려면 Enter 키를 누르세요.")

def get_window_rect(title):
    try:
        window = gw.getWindowsWithTitle(title)[0]
        if not window.isMinimized:
            return (window.left, window.top, window.width, window.height)
    except IndexError:
        return None

def detect_anchor_in_window(region):
    screenshot = pyautogui.screenshot(region=region)
    screenshot_np = np.array(screenshot)
    screenshot_gray = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2GRAY)
    return detect_anchor_multi_scale(screenshot_gray, template_gray)

def detect_anchor_multi_scale(screenshot_gray, template_gray, scales=[0.4,0.5,0.6, 0.7,0.8,0.9, 1.0, 1.25, 1.5], threshold=0.75):
    for scale in scales:
        resized_template = cv2.resize(template_gray, (0, 0), fx=scale, fy=scale)
        if resized_template.shape[0] > screenshot_gray.shape[0] or resized_template.shape[1] > screenshot_gray.shape[1]:
            continue  # 템플릿이 스크린샷보다 크면 skip
        result = cv2.matchTemplate(screenshot_gray, resized_template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)
        if max_val >= threshold:
            return True  # 일치 항목 찾음
    return False

def detection_loop():
    global detection_enabled, running
    while running:
        if detection_enabled:
            rect = get_window_rect(target_title)
            if rect:
                x, y, w, h = rect
                found = found = detect_anchor_scaled_to_window((x, y, w, h))
                if found:
                    continue
                else:
                    # print("[X] 닻 없음 → Backspace 키 누름")
                    keyboard.press_and_release('backspace')
            else:
                print("[!] 창을 찾을 수 없습니다.")
        time.sleep(1)

# 핫키 이벤트 등록
def handle_hotkeys():
    global detection_enabled, running
    keyboard.add_hotkey('f1', lambda: enable_detection())
    keyboard.add_hotkey('f2', lambda: disable_detection())

def enable_detection():
    global detection_enabled
    detection_enabled = True
    print("[▶] 감지 시작됨 (F1)")

def disable_detection():
    global detection_enabled
    detection_enabled = False
    print("[■] 감지 중단됨 (F2)")

# 스레드 실행
try:
    threading.Thread(target=detection_loop, daemon=True).start()
    handle_hotkeys()

    print("F1: 감지 시작 / F2: 감지 중지 / ESC: 종료")
    keyboard.wait('esc')  # ESC로 종료
    running = False
except Exception as e:
    print(e)
    input("...")
