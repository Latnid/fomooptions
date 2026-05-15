from datetime import datetime, timedelta
from pathlib import Path
import os
import re
import shutil
import time as t
import traceback

import pandas_market_calendars as mcal
import pytz
from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from DataBaseFlow import database_rw

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "Data"
INCREASE_DIR = DATA_DIR / "Increase"
DECREASE_DIR = DATA_DIR / "Decrease"
LOG_DIR = Path(os.getenv("OPTIONSUPDATE_LOG_DIR", Path(__file__).resolve().parent))
DEBUG_DIR = LOG_DIR / "debug"
DOWNLOAD_DIR = Path(os.getenv("SEL_DOWNLOAD_DIR", str(Path.home() / "Downloads")))
SELENIUM_REMOTE_URL = os.getenv("SELENIUM_REMOTE_URL", "http://localhost:4444/wd/hub")

DOWNLOAD_TARGETS = [
    {
        "url": "https://www.barchart.com/options/open-interest-change/increase",
        "folder": INCREASE_DIR,
        "kind": "stocks-increase",
    },
    {
        "url": "https://www.barchart.com/options/open-interest-change/decrease",
        "folder": DECREASE_DIR,
        "kind": "stocks-decrease",
    },
    {
        "url": "https://www.barchart.com/options/open-interest-change/increase?sector=etf",
        "folder": INCREASE_DIR,
        "kind": "etfs-increase",
    },
    {
        "url": "https://www.barchart.com/options/open-interest-change/decrease?sector=etf",
        "folder": DECREASE_DIR,
        "kind": "etfs-decrease",
    },
]

DOWNLOAD_SELECTORS = [
    "a.toolbar-button.download.ng-isolate-scope",
    "a.toolbar-button.download",
    "a[title*='Download']",
    "button[title*='Download']",
    "a[href*='download']",
    ".download-button",
    "[data-ng-click*='download']",
]

BLOCKING_OVERLAY_SELECTORS = [
    ".reveal-modal-bg",
    "[modal-backdrop]",
    ".modal-backdrop",
    ".modal.show",
    ".reveal-modal.open",
    ".reveal-modal[style*='display: block']",
]

MODAL_CLOSE_SELECTORS = [
    "button[aria-label='Close']",
    "[aria-label='Close']",
    "button.close",
    ".close-reveal-modal",
    ".reveal-modal .close",
    ".modal .close",
]

CSV_PATTERN = re.compile(
    r"^(stocks|etfs)-(increase|decrease)-change-in-open-interest-(\d{2}-\d{2}-\d{4})\.csv$"
)


def env_flag(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def log_error(message, exc=None):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with (LOG_DIR / "Datadownload_error.log").open("a", encoding="utf-8") as f:
        f.write(f"Error occurred at {datetime.now()}: {message}\n")
        if exc is not None:
            f.write(traceback.format_exc() + "\n")


def save_debug_artifacts(driver, label):
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_label = re.sub(r"[^A-Za-z0-9_.-]+", "_", label)
    html_path = DEBUG_DIR / f"{timestamp}_{safe_label}.html"
    png_path = DEBUG_DIR / f"{timestamp}_{safe_label}.png"
    try:
        html_path.write_text(driver.page_source, encoding="utf-8", errors="replace")
    except Exception:
        pass
    try:
        driver.save_screenshot(str(png_path))
    except Exception:
        pass
    return html_path, png_path


def assert_page_not_blocked(driver, context):
    title = driver.title or ""
    body_text = ""
    try:
        body_text = driver.find_element(By.TAG_NAME, "body").text[:1000]
    except Exception:
        pass

    blocked_markers = [
        "403 ERROR",
        "The request could not be satisfied",
        "Request blocked",
        "Access Denied",
    ]
    if any(marker in title or marker in body_text for marker in blocked_markers):
        html_path, png_path = save_debug_artifacts(driver, context)
        raise RuntimeError(
            f"Barchart blocked the browser during {context}. "
            f"Title={title!r}. Debug HTML={html_path}, screenshot={png_path}"
        )


def create_driver():
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_experimental_option(
        "prefs",
        {
            "download.default_directory": str(DOWNLOAD_DIR),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
        },
    )

    driver = webdriver.Remote(
        command_executor=SELENIUM_REMOTE_URL,
        options=chrome_options,
    )
    driver.set_page_load_timeout(int(os.getenv("OPTIONSUPDATE_PAGE_LOAD_TIMEOUT", "90")))
    return driver


def login(driver):
    wait = WebDriverWait(driver, int(os.getenv("OPTIONSUPDATE_WAIT_TIMEOUT", "45")))
    driver.get("https://www.barchart.com/login")
    assert_page_not_blocked(driver, "login_page")

    try:
        username_input = wait.until(EC.presence_of_element_located((By.NAME, "email")))
        password_input = wait.until(EC.presence_of_element_located((By.NAME, "password")))
    except TimeoutException as exc:
        html_path, png_path = save_debug_artifacts(driver, "login_fields_missing")
        raise RuntimeError(
            f"Login form was not found. Debug HTML={html_path}, screenshot={png_path}"
        ) from exc

    username_input.clear()
    username_input.send_keys(os.getenv("username"))
    password_input.clear()
    password_input.send_keys(os.getenv("password"))
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))).click()
    t.sleep(6)
    assert_page_not_blocked(driver, "after_login")

    if driver.find_elements(By.NAME, "email") and "login" in driver.current_url.lower():
        html_path, png_path = save_debug_artifacts(driver, "login_failed")
        raise RuntimeError(
            f"Login did not complete. Current URL={driver.current_url}. "
            f"Debug HTML={html_path}, screenshot={png_path}"
        )


def find_download_button(driver, wait):
    for selector in DOWNLOAD_SELECTORS:
        try:
            button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
            if button.is_displayed() and button.is_enabled():
                return button
        except TimeoutException:
            continue
    return None


def wait_for_download(before_files, started_at, timeout=120):
    deadline = t.time() + timeout
    while t.time() < deadline:
        partials = list(DOWNLOAD_DIR.glob("*.crdownload"))
        csv_files = [
            path
            for path in DOWNLOAD_DIR.glob("*.csv")
            if path not in before_files and path.stat().st_mtime >= started_at
        ]
        if csv_files and not partials:
            return max(csv_files, key=lambda p: p.stat().st_mtime)
        t.sleep(1)
    raise TimeoutError(f"No completed CSV download appeared in {DOWNLOAD_DIR} within {timeout}s")


def maybe_click_download_anyway(driver):
    selectors = [
        'button[data-ng-click="redirectToDownload(true)"]',
        "button.download-anyway",
        "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'download anyway')]",
    ]
    for selector in selectors:
        try:
            if selector.startswith("//"):
                buttons = driver.find_elements(By.XPATH, selector)
            else:
                buttons = driver.find_elements(By.CSS_SELECTOR, selector)
            for button in buttons:
                if button.is_displayed() and button.is_enabled():
                    button.click()
                    return True
        except Exception:
            continue
    return False


def has_visible_blocking_overlay(driver):
    for selector in BLOCKING_OVERLAY_SELECTORS:
        try:
            if any(element.is_displayed() for element in driver.find_elements(By.CSS_SELECTOR, selector)):
                return True
        except Exception:
            continue
    return False


def close_blocking_overlays(driver):
    closed_any = False
    for _ in range(3):
        if not has_visible_blocking_overlay(driver):
            return closed_any

        if maybe_click_download_anyway(driver):
            return True

        for selector in MODAL_CLOSE_SELECTORS:
            try:
                for element in driver.find_elements(By.CSS_SELECTOR, selector):
                    if element.is_displayed() and element.is_enabled():
                        element.click()
                        t.sleep(1)
                        closed_any = True
                        break
                if closed_any and not has_visible_blocking_overlay(driver):
                    return True
            except Exception:
                continue

        try:
            driver.switch_to.active_element.send_keys("\ue00c")  # Escape
            t.sleep(1)
            closed_any = True
        except Exception:
            pass

        if not has_visible_blocking_overlay(driver):
            return closed_any

        for selector in [".reveal-modal-bg", "[modal-backdrop]", ".modal-backdrop"]:
            try:
                for element in driver.find_elements(By.CSS_SELECTOR, selector):
                    if element.is_displayed():
                        element.click()
                        t.sleep(1)
                        closed_any = True
                        break
            except Exception:
                continue

    return closed_any


def click_download_button(driver, button, target_kind):
    close_blocking_overlays(driver)
    driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", button)
    t.sleep(1)

    last_error = None
    for attempt in range(1, 4):
        try:
            button.click()
            return
        except ElementClickInterceptedException as exc:
            last_error = exc
            save_debug_artifacts(driver, f"download_click_intercepted_{target_kind}_attempt_{attempt}")

            if maybe_click_download_anyway(driver):
                return

            if close_blocking_overlays(driver):
                t.sleep(1)
                continue

            try:
                driver.execute_script("arguments[0].click();", button)
                return
            except Exception as js_exc:
                last_error = js_exc
                t.sleep(1)

    raise last_error


def download_csv():
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    INCREASE_DIR.mkdir(parents=True, exist_ok=True)
    DECREASE_DIR.mkdir(parents=True, exist_ok=True)

    driver = create_driver()
    downloaded_files = []
    wait = WebDriverWait(driver, int(os.getenv("OPTIONSUPDATE_WAIT_TIMEOUT", "45")))
    try:
        login(driver)

        for target in DOWNLOAD_TARGETS:
            url = target["url"]
            folder_path = target["folder"]
            driver.get(url)
            t.sleep(5)
            assert_page_not_blocked(driver, f"data_page_{target['kind']}")

            button = find_download_button(driver, wait)
            if button is None:
                html_path, png_path = save_debug_artifacts(driver, f"download_button_missing_{target['kind']}")
                raise RuntimeError(
                    f"Download button not found on {url}. "
                    f"Debug HTML={html_path}, screenshot={png_path}"
                )

            before_files = set(DOWNLOAD_DIR.glob("*"))
            started_at = t.time()
            click_download_button(driver, button, target["kind"])
            t.sleep(3)
            if maybe_click_download_anyway(driver):
                t.sleep(3)

            source_file = wait_for_download(
                before_files,
                started_at,
                timeout=int(os.getenv("OPTIONSUPDATE_DOWNLOAD_TIMEOUT", "120")),
            )
            destination_file = folder_path / source_file.name
            if destination_file.exists():
                destination_file.unlink()
            shutil.move(str(source_file), str(destination_file))
            downloaded_files.append(destination_file)
            print(f"{source_file.name} downloaded and saved to {destination_file} successfully!", flush=True)

        return downloaded_files
    finally:
        driver.quit()


def parse_csv_name(path):
    match = CSV_PATTERN.match(path.name)
    if not match:
        return None
    types, direction, date = match.groups()
    return types, direction, date


def complete_dates():
    by_date = {}
    for path in list(INCREASE_DIR.glob("*.csv")) + list(DECREASE_DIR.glob("*.csv")):
        parsed = parse_csv_name(path)
        if not parsed:
            continue
        types, direction, date = parsed
        by_date.setdefault(date, {})[(types, direction)] = path

    required = {
        ("stocks", "increase"),
        ("stocks", "decrease"),
        ("etfs", "increase"),
        ("etfs", "decrease"),
    }
    return {
        date: files
        for date, files in by_date.items()
        if required.issubset(files.keys())
    }


def latest_complete_date():
    dates = complete_dates()
    if not dates:
        return None, None
    date = max(dates, key=lambda d: datetime.strptime(d, "%m-%d-%Y"))
    return date, dates[date]


def write_data_to_database(directory=None, date=None):
    if date is None:
        date, files = latest_complete_date()
    else:
        files = complete_dates().get(date)

    if not date or not files:
        raise FileNotFoundError("No complete CSV set found for database write.")

    csv_time = max(path.stat().st_mtime for path in files.values())
    print(f"Writing complete CSV set for {date} to database.", flush=True)
    for types in ["stocks", "etfs"]:
        database_rw(
            operation="write",
            date=date,
            csv_time=csv_time,
            types=types,
            BDTE="min",
            EDTE="max",
        )


def clean_csv():
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    for path in DOWNLOAD_DIR.iterdir():
        if path.suffix in {".csv", ".crdownload"}:
            path.unlink()
    print(".csv files cleaned", flush=True)


def is_trading_hours(current_time):
    """Return True during NYSE regular trading hours used by this updater."""
    nyse = mcal.get_calendar("NYSE")
    trading_dates = nyse.schedule(start_date=current_time.date(), end_date=current_time.date())
    if len(trading_dates) == 0:
        return False

    trading_start_time = datetime.strptime("9:45", "%H:%M").time()
    trading_end_time = datetime.strptime("16:00", "%H:%M").time()
    return trading_start_time <= current_time.time() <= trading_end_time


def run_cycle():
    clean_csv()
    download_csv()
    if env_flag("OPTIONSUPDATE_SKIP_DATABASE_WRITE"):
        print("OPTIONSUPDATE_SKIP_DATABASE_WRITE is set; skipping database write.", flush=True)
        return
    write_data_to_database()


def countdown(seconds, message):
    mins, secs = divmod(max(seconds, 0), 60)
    print(f"{message} {mins:02d}:{secs:02d}.", flush=True)
    if seconds > 0:
        t.sleep(seconds)


if __name__ == "__main__":
    run_once = env_flag("OPTIONSUPDATE_RUN_ONCE")
    ignore_market_hours = env_flag("OPTIONSUPDATE_IGNORE_MARKET_HOURS")

    while True:
        try:
            us_eastern_tz = pytz.timezone("America/New_York")
            current_time = datetime.now(us_eastern_tz)
            if ignore_market_hours or is_trading_hours(current_time):
                print(f"{current_time} - Running OptionsUpdate cycle...", flush=True)
                run_cycle()
                if run_once:
                    break
                print("Repeat in 20 minutes.", flush=True)
                countdown(20 * 60, "Next download in")
            else:
                next_minute = (current_time + timedelta(minutes=1)).replace(second=0, microsecond=0)
                wait_seconds = max(1, int((next_minute - current_time).total_seconds()))
                if run_once:
                    print(f"{current_time} - Market closed; run once requested, exiting.", flush=True)
                    break
                countdown(wait_seconds, f"Market closed. Next checking time is {next_minute}. Waiting")
        except Exception as e:
            log_error(str(e), e)
            if run_once:
                raise
            countdown(60, "Cycle failed. Retrying in")
