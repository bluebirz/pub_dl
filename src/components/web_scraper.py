import time
from dataclasses import asdict, dataclass
from pathlib import Path

from bs4 import BeautifulSoup

# from fake_useragent import UserAgent
from patchright.sync_api import sync_playwright as patchright
from playwright.sync_api import sync_playwright as playwright
from tenacity import retry, retry_if_result, stop_after_attempt, wait_fixed

from components.file_manager import get_filesize, is_exists

PLAYWRIGHT_ARGS = [
    "–-disable-blink-features=AutomationControlled",
    # "–-disable-dev-shm-usage",
    # "--disable-background-timer-throttling",
    # "--disable-gpu",
    # "–-no-sandbox",
    # "-–disable-setuid-sandbox",
    # "-–disable-web-security",
    # "–-disable-features=IsolateOrigins,site-per-process",
]
BROWSER_CONTEXT = {
    "viewport": {"width": 720, "height": 480},
    # "locale": "en-US",
    # "timezone_id": "Europe/Stockholm",
    # "user_agent": UserAgent().chrome,
    # "java_script_enabled": True,
    # "ignore_https_errors": False,
}
DEFAULT_TIMEOUT = 60_000


@dataclass
class WebScraper:
    url: str
    is_headless: bool = True
    user_data_dir: str = None

    def __launch_headless(self) -> None:
        self.browser = self.pw.chromium.launch(headless=True)
        self.context = self.browser.new_context(**BROWSER_CONTEXT)
        self.context.set_default_timeout(DEFAULT_TIMEOUT)
        self.page = self.context.new_page()

    def __launch_headful(self) -> None:
        if not self.user_data_dir:
            raise ValueError("user_data_dir is required when is_headless is False")
        self.browser = self.pw.chromium.launch_persistent_context(
            user_data_dir=(Path("user_data") / Path(self.user_data_dir)).as_posix(),
            headless=False,
            channel="chrome",
            **BROWSER_CONTEXT,
            # viewport=BROWSER_CONTEXT.get("viewport"),
        )
        self.browser.set_default_timeout(DEFAULT_TIMEOUT)
        self.page = self.browser.new_page()

    def __post_init__(self):
        if self.is_headless:
            self.pw = playwright().start()
            self.__launch_headless()
        else:
            self.pw = patchright().start()
            # self.pw = playwright().start()
            self.__launch_headful()

    def __enter__(self):
        self.page.goto(self.url)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.browser.close()
        self.pw.stop()

    @retry(
        retry=retry_if_result(lambda r: isinstance(r, tuple) and r[0] is False),
        wait=wait_fixed(2),
        stop=stop_after_attempt(3),
        retry_error_callback=lambda retry_state: retry_state.outcome.result(),
    )
    def download(self, img_url: str, img_download_path: str) -> tuple[bool, str]:
        """
        return
        - bool = True if download success
        - download message string
        """
        if is_exists(img_download_path, True):
            return None, "File already exists"
        req = self.browser.new_context() if self.is_headless else self.browser
        res = req.request.get(img_url)
        if not res.ok:
            return False, res.status_text
        with open(img_download_path, "wb") as fptr:
            fptr.write(res.body())
        if is_exists(img_download_path) and get_filesize(img_download_path) > 0:
            return True, None
        else:
            return False, "Downloaded file missing or corrupted"

    def check_cloudflare_turnstile(self, timeout=5):
        """Poll for the Turnstile response token after manual click."""
        start = time.time()
        while time.time() - start < timeout:
            token = self.page.evaluate("""
                () => {
                    const el = document.querySelector('input[name="cf-turnstile-response"]');
                    return el ? el.value : '';
                }
            """)
            if token and len(token) > 20:
                self.page.wait_for_load_state("networkidle")
                return token
            time.sleep(0.5)
        return None

    def get_html(self) -> BeautifulSoup:
        if self.page.url is None:
            raise ValueError("No URL the page is landed")
        if (html_content := self.page.content()) is None:
            raise ValueError("No contents.")
        return BeautifulSoup(html_content, "html.parser")


@dataclass
class WebScraperStats:
    num_new: int = 0
    num_err: int = 0
    num_dup: int = 0

    def add_stats(self, s: bool | None) -> None:
        if s is True:
            self.num_new += 1
        elif s is False:
            self.num_err += 1
        else:
            self.num_dup += 1

    def tostring(self) -> str:
        return f"status: new ={self.num_new: d} / error ={self.num_err: d} / exists ={self.num_dup: d}"


@dataclass
class WebScraperResult:
    status: bool = True
    status_text: str = None
    input_url: str = None
    output_folder: str = None
    is_output_folder_exists: bool = False
    num_img_total: int = 0
    num_img_stats: WebScraperStats = None

    def todict(self):
        return asdict(self)
