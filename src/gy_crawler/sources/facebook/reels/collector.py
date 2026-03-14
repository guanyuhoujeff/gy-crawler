from .parser import extract_caption_from_html, extract_publish_time_from_html
from .paths import canonicalize_reel_url, extract_reel_id


VISIBLE_REELS_SCRIPT = """
(limit) => {
  const anchors = Array.from(document.querySelectorAll('a[href]'));
  const isVisible = (el) => {
    const style = window.getComputedStyle(el);
    const rect = el.getBoundingClientRect();
    return style.visibility !== 'hidden' && style.display !== 'none' && rect.width > 0 && rect.height > 0;
  };
  const results = [];
  for (const anchor of anchors) {
    const href = anchor.getAttribute('href') || '';
    if (!href.includes('/reel/')) continue;
    if (!isVisible(anchor)) continue;
    const reelUrl = new URL(href, location.origin).toString();
    const text = (anchor.textContent || '').trim().replace(/\\s+/g, ' ');
    results.push({ href: reelUrl, text });
    if (results.length >= limit * 3) break;
  }
  return results;
}
"""


def _scroll_page(page):
    if hasattr(page, "mouse") and hasattr(page.mouse, "wheel"):
        page.mouse.wheel(0, 3000)
    else:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")


def collect_visible_reels(
    page,
    limit,
    scroll=True,
    max_scrolls=10,
    max_idle_scrolls=2,
    delay_ms=1000,
):
    raw_items = page.evaluate(VISIBLE_REELS_SCRIPT, limit)
    reels = []
    seen = set()
    scrolls = 0
    idle_scrolls = 0

    while True:
        new_count = 0
        for item in raw_items:
            reel_url = canonicalize_reel_url(item["href"])
            if reel_url in seen:
                continue
            seen.add(reel_url)
            new_count += 1
            reels.append(
                {
                    "reel_url": reel_url,
                    "view_count_visible": item.get("text") or None,
                }
            )
            if len(reels) >= limit:
                break

        if len(reels) >= limit or not scroll or scrolls >= max_scrolls:
            break

        if new_count == 0:
            idle_scrolls += 1
        else:
            idle_scrolls = 0
        if idle_scrolls >= max_idle_scrolls:
            break

        _scroll_page(page)
        if hasattr(page, "wait_for_timeout"):
            page.wait_for_timeout(delay_ms)
        scrolls += 1
        raw_items = page.evaluate(VISIBLE_REELS_SCRIPT, limit)

    return reels


class PlaywrightFacebookCollector:
    def __init__(self, headless=True, delay_seconds=1.5):
        self.headless = headless
        self.delay_seconds = delay_seconds
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

    def __enter__(self):
        from playwright.sync_api import sync_playwright

        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=self.headless)
        self._context = self._browser.new_context()
        self._page = self._context.new_page()
        return self

    def __exit__(self, exc_type, exc, tb):
        if self._context is not None:
            self._context.close()
        if self._browser is not None:
            self._browser.close()
        if self._playwright is not None:
            self._playwright.stop()

    def _goto(self, url):
        self._page.goto(url, wait_until="domcontentloaded")
        self._page.wait_for_timeout(int(self.delay_seconds * 1000))

    def collect_profile(
        self,
        profile_url,
        limit,
        scroll=True,
        max_scrolls=10,
        max_idle_scrolls=2,
    ):
        self._goto(profile_url)
        account_name = self._page.locator("h1").first.inner_text().strip()
        reels = collect_visible_reels(
            self._page,
            limit=limit,
            scroll=scroll,
            max_scrolls=max_scrolls,
            max_idle_scrolls=max_idle_scrolls,
            delay_ms=int(self.delay_seconds * 1000),
        )
        if not reels:
            raise RuntimeError("Profile collection failed: no visible reels found")
        return {
            "account_name": account_name,
            "source_profile_url": self._page.url,
            "reels": reels,
        }

    def collect_reel_detail(self, reel_url):
        self._goto(reel_url)
        html = self._page.content()
        detail = extract_publish_time_from_html(html, reel_id=extract_reel_id(reel_url))
        detail["caption"] = extract_caption_from_html(html)
        if not detail.get("caption"):
            title = self._page.title().strip()
            detail["caption"] = title or None
        return detail
