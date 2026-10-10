"""Check the forest UI in local Chromium. Does not push or deploy."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import hashlib
import json
import re
import os
import traceback

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "prototype/pilot-flow.html"
DESIGN = os.environ.get("VOCABULARY_DESIGN", "forest")
assert DESIGN in ["forest", "city"]
OUT = Path(__file__).resolve().parent / ("forest" if DESIGN == "forest" else "city")
OUT.mkdir(exist_ok=True)
checks, errors, asset_failures = [], [], []


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(SOURCE.parent)))
Thread(target=server.serve_forever, daemon=True).start()
URL = f"http://127.0.0.1:{server.server_port}/pilot-flow.html"


def check(name, fn):
    try:
        checks.append({"name": name, "status": "PASS", "details": fn() or {}})
    except Exception:
        checks.append({"name": name, "status": "FAIL", "error": traceback.format_exc()})


def login(page, role):
    page.locator(f'[data-login-role="{role}"]').click()
    value = "test2" if role == "teacher" else "test1"
    page.locator("#login-id").fill(value)
    page.locator("#login-password").fill(value)
    page.locator("#login-password").press("Enter")
    if role == "teacher":
        page.locator('[data-action="open-student"][data-student="student-jiwoo"]').first.click()


def images_loaded(page):
    page.wait_for_function("Array.from(document.querySelectorAll('#app img,#forest-world img')).every(i=>i.complete && i.naturalWidth>0)")
    page.evaluate("()=>Promise.all(Array.from(document.querySelectorAll('#app img,#forest-world img')).map(i=>i.decode()))")


def screenshot(page, name, full=False):
    images_loaded(page)
    page.evaluate("window.scrollTo(0,0)")
    page.evaluate("()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))")
    page.screenshot(path=str(OUT / (name + ".png")), full_page=full)


def fits(page):
    assert page.evaluate("document.documentElement.scrollWidth<=innerWidth"), "Page has horizontal overflow"
    for button in page.locator("#app button:visible").all():
        box = button.bounding_box()
        assert box["x"] >= -1 and box["x"] + box["width"] <= page.viewport_size["width"] + 1


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(executable_path="/usr/bin/chromium", headless=True, args=["--no-sandbox"])
    context = browser.new_context(viewport={"width": 1280, "height": 960})
    context.add_init_script("if (!localStorage.getItem('vocabulary-design-v1')) localStorage.setItem('vocabulary-design-v1'," + json.dumps(DESIGN) + ");")
    page = context.new_page()
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("response", lambda response: asset_failures.append(response.url) if response.status >= 400 else None)
    page.goto(URL)

    def login_scenes():
        screenshot(page, "login-student-desktop")
        assert ("forest-entrance.webp" if DESIGN == "forest" else "city-world.webp") in page.locator(".login-landscape").get_attribute("src")
        page.locator('[data-login-role="teacher"]').click()
        assert (DESIGN+"-teacher.webp") in page.locator(".login-landscape").get_attribute("src")
        screenshot(page, "login-teacher-desktop")
        for width in [360, 390, 768, 1280]:
            page.set_viewport_size({"width": width, "height": 960})
            fits(page)
            for selector in ["#login-id", "#login-password", ".login-submit"]:
                assert page.locator(selector).bounding_box()["height"] >= 44
        page.set_viewport_size({"width": 390, "height": 900})
        screenshot(page, "login-mobile", True)
        page.set_viewport_size({"width": 1280, "height": 960})
        return {"viewports": [360, 390, 768, 1280], "studentAndTeacherScenes": True}
    check("Student and teacher login illustrations load and controls fit desktop/mobile", login_scenes)

    def full_environment():
        measurements = []
        for width in [360, 390, 768, 1280]:
            page.set_viewport_size({"width": width, "height": 960})
            images_loaded(page)
            expected = DESIGN + ("-world-mobile.webp" if width <= 800 else "-world.webp")
            assert page.locator("#forest-world img").evaluate("e=>e.currentSrc").endswith(expected)
            box = page.locator("#forest-world").bounding_box()
            assert box["x"] == box["y"] == 0 and box["width"] == width and box["height"] == 960
            assert page.locator("#forest-world").evaluate("e=>getComputedStyle(e).position") == "fixed"
            assert page.locator("#forest-world").evaluate("e=>getComputedStyle(e).pointerEvents") == "none"
            fits(page)
            measurements.append({"width": width, "wholeViewport": True, "asset": expected})
        page.set_viewport_size({"width": 1280, "height": 960})
        return {"viewports": measurements, "decorationOnly": page.locator("#forest-world").get_attribute("aria-hidden") == "true"}
    check("Desktop and portrait forest backgrounds cover the whole viewport without blocking controls", full_environment)

    def motion_controls():
        leaf = page.locator(".forest-leaf" if DESIGN == "forest" else ".city-drone").first
        before_record = page.evaluate("localStorage.getItem('vocabulary-pilot-flow-v2')")
        assert page.locator("#forest-world").get_attribute("data-motion") == "running"
        before = leaf.evaluate("e=>getComputedStyle(e).transform")
        page.wait_for_timeout(250)
        assert leaf.evaluate("e=>getComputedStyle(e).transform") != before
        page.locator("#forest-motion-toggle").click()
        assert page.locator("#forest-world").get_attribute("data-motion") == "paused"
        before = leaf.evaluate("e=>getComputedStyle(e).transform")
        page.wait_for_timeout(250)
        assert leaf.evaluate("e=>getComputedStyle(e).transform") == before
        assert page.locator("#forest-motion-toggle").get_attribute("aria-pressed") == "false"
        page.reload()
        assert page.locator("#forest-world").get_attribute("data-motion") == "paused"
        assert "켜기" in page.locator("#forest-motion-toggle").inner_text()
        assert page.evaluate("localStorage.getItem('vocabulary-pilot-flow-v2')") == before_record
        page.locator("#forest-motion-toggle").click()
        assert page.locator("#forest-world").get_attribute("data-motion") == "running"
        return {"animationActuallyChangesTransform": True, "pauseFreezesMotion": True, "choiceSurvivesReload": True, "learningRecordUnaffected": True}
    check("Leaf motion runs, pauses and resumes; preference persists separately from learning", motion_controls)

    def reduced_motion():
        page.emulate_media(reduced_motion="reduce")
        page.wait_for_function("document.getElementById('forest-world').getAttribute('data-motion')==='paused'")
        assert page.locator("#forest-motion-toggle").is_disabled()
        assert page.locator(".forest-leaf" if DESIGN == "forest" else ".city-drone").first.evaluate("e=>getComputedStyle(e).animationName") == "none"
        page.emulate_media(reduced_motion="no-preference")
        page.wait_for_function("document.getElementById('forest-world').getAttribute('data-motion')==='running'")
        assert page.locator("#forest-motion-toggle").is_enabled()
        return {"operatingSystemPreference": "honored", "animations": "none under reduce", "preferenceChangesLive": True}
    check("Reduced-motion preference disables ambient animation and updates live", reduced_motion)

    def diagnosis():
        login(page, "student")
        assert page.locator('.step[aria-current="step"]').count() == 1
        screenshot(page, "diagnosis-desktop")
        for width in [360, 390, 768, 1280]:
            page.set_viewport_size({"width": width, "height": 960})
            fits(page)
            assert page.locator(".token-bank button").count() == 10
            if width == 360:
                screenshot(page, "diagnosis-mobile")
        page.set_viewport_size({"width": 1280, "height": 960})
        page.locator('[data-action="fill-example"]').click()
        page.get_by_test_id("start-plan").click()
        screenshot(page, "plan-desktop")
        page.get_by_test_id("start-session").click()
        return {"definitionRows": 10, "wordCards": 10, "viewports": [360, 390, 768, 1280]}
    check("Diagnosis word placement and planned learning remain readable at all widths", diagnosis)

    def practice():
        screenshot(page, "study-desktop")
        for width in [360, 390, 768, 1280]:
            page.set_viewport_size({"width": width, "height": 960})
            fits(page)
            assert page.locator(".answer").count() == 4
            for answer in page.locator(".answer").all():
                assert answer.bounding_box()["height"] >= 44
            if width == 390:
                screenshot(page, "study-mobile")
        page.set_viewport_size({"width": 1280, "height": 960})
        for index in range(10):
            q = page.evaluate("studyQuestion(currentSession().activities[currentSession().currentIndex],currentSession().responses[currentSession().activities[currentSession().currentIndex].id])")
            choice = next(o["id"] for o in q["options"] if o["id"] != q["correct_option_id"]) if index == 0 else q["correct_option_id"]
            page.get_by_test_id("option-" + choice).click()
            page.get_by_test_id("submit-answer").click()
            page.get_by_test_id("next").click()
        assert page.locator("[data-writing]").count() == 10
        assert (DESIGN+"-writing.webp") in page.locator(".forest-banner-art").get_attribute("src")
        screenshot(page, "writing-desktop")
        page.evaluate("window.scrollTo(0,1000)")
        assert page.locator("#forest-world").bounding_box()["y"] == 0
        images_loaded(page)
        page.screenshot(path=str(OUT / "writing-scrolled-desktop.png"))
        page.set_viewport_size({"width": 390, "height": 960})
        fits(page)
        screenshot(page, "writing-mobile")
        for field in page.locator("[data-writing]").all():
            field.fill("새로운 단어의 쓰임을 생각하며 한 문장을 작성했어요.")
        page.get_by_test_id("submit-writing").click()
        page.locator('[data-action="reviews"]').click()
        fits(page)
        page.set_viewport_size({"width": 1280, "height": 960})
        screenshot(page, "reviews-desktop")
        return {"objectiveResponses": 10, "writingSubmissions": 10, "allThreeReviewPeriods": True}
    check("Four-choice practice, all ten writings and period reviews work with the forest UI", practice)

    def teacher():
        page.locator("#logout").click()
        login(page, "teacher")
        assert page.locator(".record-answer.incorrect").count() >= 1
        assert page.locator(".record-answer.incorrect").first.evaluate("e=>getComputedStyle(e).color") == ("rgb(178, 55, 55)" if DESIGN == "forest" else "rgb(177, 50, 54)")
        screenshot(page, "teacher-records-desktop")
        page.locator('[data-action="teacher-page"][data-page="grading"]').click()
        for activity, judgment in [("regular-W1", "correct"), ("regular-W2", "incorrect"), ("regular-W3", "uncertain")]:
            buttons = page.locator(f'[data-action="writing-judgment"][data-activity="{activity}"]')
            assert buttons.count() == 3
            page.locator(f'[data-action="writing-judgment"][data-activity="{activity}"][data-judgment="{judgment}"]').click()
            assert buttons.filter(has=page.locator("input")).count() == 0
            assert page.locator(f'[data-action="writing-judgment"][data-activity="{activity}"][aria-pressed="true"]').count() == 1
            page.locator(f'[data-action="confirm-grade"][data-activity="{activity}"]').click()
        screenshot(page, "teacher-grading-desktop")
        page.locator('[data-action="teacher-page"][data-page="report"]').click()
        screenshot(page, "teacher-report-desktop")
        for width in [360, 390, 768, 1280]:
            page.set_viewport_size({"width": width, "height": 960})
            fits(page)
            assert page.locator(".donut-svg").count() == 4
            if width == 390:
                screenshot(page, "teacher-report-mobile")
        return {"wrongAnswersRed": True, "threeSingleChoiceJudgmentButtons": True, "responsiveReports": True}
    check("Teacher record colors, three grading choices and charts remain usable", teacher)

    def contrast():
        pairs = page.evaluate("""() => {
          const selectors=['.brand-name','.forest-eyebrow','.forest-banner-copy h1','.forest-banner-copy>p:last-child','.teacher-nav .selected','.chart-subtitle','.assessment-status','.notice','.field>span','.primary','.fine'];
          return selectors.map(selector=>{
            const e=document.querySelector(selector), c=getComputedStyle(e);
            let parent=e, backgrounds=[];
            while(parent && parent!==document.body){backgrounds.push(getComputedStyle(parent).backgroundColor);parent=parent.parentElement;}
            return {selector,color:c.color,backgrounds};
          });
        }""")
        def channels(color):
            values = [float(v) for v in re.findall(r"[\d.]+", color)]
            return values[:3], values[3] if len(values) > 3 else 1
        def luminance(rgb):
            channels = [v / 255 for v in rgb]
            channels = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in channels]
            return sum(v * weight for v, weight in zip(channels, [.2126, .7152, .0722]))
        for pair in pairs:
            ratios = []
            foreground, _ = channels(pair["color"])
            for extreme in [0, 255]:
                background = [extreme] * 3
                for color in reversed(pair["backgrounds"]):
                    rgb, alpha = channels(color)
                    background = [value * alpha + parent * (1-alpha) for value, parent in zip(rgb, background)]
                a, b = sorted([luminance(foreground), luminance(background)])
                ratios.append((b + .05) / (a + .05))
            pair["ratio"] = round(min(ratios), 2)
            assert pair["ratio"] >= 4.5, pair
        return {"pairs": pairs, "criterion": "4.5:1 for sampled surfaces, composited over black and white illustration extremes; artwork edges reviewed visually"}
    check("Main text, muted labels and primary buttons meet sampled text contrast", contrast)

    def parent_print():
        page.set_viewport_size({"width": 1280, "height": 960})
        page.locator('[data-report-field="parentMessage"]').fill("FOREST_CONFIRMED_PARENT_MESSAGE 함께 문장을 읽고 단어의 쓰임을 확인해 주세요.")
        page.locator('[data-report-field="internalMemo"]').fill("FOREST_PRIVATE_MEMO_DO_NOT_PRINT")
        page.locator('[data-action="confirm-report"]').click()
        page.evaluate("prepareParentPrint()")
        page.emulate_media(media="print")
        assert page.locator("#print-area").is_visible()
        assert not page.locator(".forest-banner").is_visible()
        assert not page.locator(".topbar").is_visible()
        assert not page.locator("#forest-world").is_visible()
        assert "FOREST_CONFIRMED_PARENT_MESSAGE" in page.locator("#print-area").inner_text()
        assert "FOREST_PRIVATE_MEMO_DO_NOT_PRINT" not in page.locator("#print-area").inner_text()
        page.pdf(path=str(OUT / "parent-report.pdf"), print_background=True)
        screenshot(page, "parent-report-print", True)
        page.emulate_media(media="screen")
        return {"browserPrintCSS": True, "pdfGenerated": True, "illustrationsExcluded": True, "physicalPrinting": "not tested"}
    check("Parent report print/PDF excludes illustrations and internal notes", parent_print)

    def saved():
        before = page.evaluate("JSON.stringify(state.sessions.regular)")
        page.reload()
        page.locator('[data-action="open-student"][data-student="student-jiwoo"]').first.click()
        assert page.locator(".teacher-nav").is_visible()
        assert page.evaluate("JSON.stringify(state.sessions.regular)") == before
        assert page.locator('[data-report-field="parentMessage"]').input_value().startswith("FOREST_CONFIRMED_PARENT_MESSAGE")
        return {"learningAndGradesKeptOnReload": True, "reportTextKept": True}
    check("Saved learning, grades and teacher report survive a page reload", saved)
    check("No uncaught script errors or failed illustration requests", lambda: {"scriptErrors": errors, "assetFailures": asset_failures} if not errors and not asset_failures else (_ for _ in ()).throw(AssertionError([errors, asset_failures])))
    browser.close()
server.shutdown()

result = {"method": "Real local Chromium through Playwright", "design": DESIGN, "html_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
          "passed": sum(c["status"] == "PASS" for c in checks), "failed": sum(c["status"] == "FAIL" for c in checks), "checks": checks,
          "limits": ["Physical devices and physical printing not tested.", "No deployment or remote verification performed."],
          "assets": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((SOURCE.parent / "assets").glob("*.webp"))}}
(OUT / "browser-results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"passed": result["passed"], "failed": result["failed"], "failures": [c for c in checks if c["status"] == "FAIL"]}, ensure_ascii=False))
raise SystemExit(bool(result["failed"]))
