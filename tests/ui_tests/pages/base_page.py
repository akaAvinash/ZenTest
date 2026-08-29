from utils.logger import get_logger


class BasePage:
    def __init__(self, page):
        self.page = page
        self.logger = get_logger(self.__class__.__module__)

    def toast(self):
        """The shared toast notification element (#toast), present on every page."""
        return self.page.locator("#toast")

    def toast_text_now(self) -> str:
        """Best-effort snapshot of the toast's current text — "" if it
        isn't present/rendered yet. Meant to be captured right before an
        action that will trigger a new toast, then passed to
        wait_for_toast() so a stale, still-visible toast from a *previous*
        action isn't mistaken for this one."""
        try:
            return self.toast().inner_text(timeout=200).strip()
        except Exception:
            return ""

    def wait_for_toast(self, previous_text: str = "", timeout: int = 5000):
        """Waits for the toast to show a genuinely NEW message: its 'show'
        class applied AND its text different from `previous_text`.

        Two things make a naive wait insufficient here: (1) #toast always
        has a non-zero bounding box (hidden via CSS opacity, not
        display:none), so plain Locator.wait_for() considers it "visible"
        from page load, well before 'show' is ever applied; and (2) toasts
        stay in the 'show' state for ~2.5s, so two actions performed in
        quick succession can have the second one's wait resolve instantly
        against the FIRST action's still-visible toast unless we also
        check the text actually changed.
        """
        self.page.wait_for_function(
            """(prevText) => {
                const el = document.getElementById('toast');
                return !!el && el.classList.contains('show') && el.textContent.trim() !== prevText;
            }""",
            arg=previous_text,
            timeout=timeout,
        )
        return self.toast()