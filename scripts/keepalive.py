"""
Streamlit Community Cloud 앱 깨우기 스크립트
------------------------------------------
단순 HTTP GET(curl 등)은 정적 HTML 껍데기만 받아오고 실제 앱을 깨우지 못합니다.
Playwright로 실제 브라우저 방문을 시뮬레이션해서 sleep 상태를 해제합니다.
"""

from playwright.sync_api import sync_playwright
import sys

# 여기에 본인 앱 URL을 입력하세요 (여러 개 가능)
APP_URLS = [
    "https://healthlab.streamlit.app/",
]

WAKE_BUTTON_TEXT = "Yes, get this app back up!"


def wake_app(playwright, url: str) -> bool:
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()
    try:
        page.goto(url, timeout=30000, wait_until="networkidle")

        # sleep 상태면 깨우기 버튼이 뜸
        wake_button = page.get_by_text(WAKE_BUTTON_TEXT, exact=False)
        if wake_button.is_visible(timeout=5000):
            print(f"[SLEEPING] {url} → 깨우기 버튼 클릭")
            wake_button.click()
            page.wait_for_timeout(15000)  # 앱이 재기동할 시간을 줌
            print(f"[WOKE UP] {url}")
        else:
            print(f"[OK] {url} 이미 활성 상태")
        return True
    except Exception as e:
        print(f"[ERROR] {url}: {e}")
        return False
    finally:
        browser.close()


def main():
    all_ok = True
    with sync_playwright() as p:
        for url in APP_URLS:
            ok = wake_app(p, url)
            all_ok = all_ok and ok

    if not all_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
