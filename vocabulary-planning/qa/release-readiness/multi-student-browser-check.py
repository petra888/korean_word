"""Real local Chromium: teacher roster, two students, isolated records and print."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import hashlib
import json
import traceback
from playwright.sync_api import sync_playwright

SOURCE = Path(__file__).resolve().parents[2] / "prototype/pilot-flow.html"
OUT = Path(__file__).resolve().parent / "multi-student"
OUT.mkdir(exist_ok=True)
checks, errors, failed_requests = [], [], []

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_): pass

server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(SOURCE.parent)))
Thread(target=server.serve_forever, daemon=True).start()
URL = f"http://127.0.0.1:{server.server_port}/pilot-flow.html"

def check(name, fn):
    try: checks.append({"name": name, "status": "PASS", "details": fn() or {}})
    except Exception: checks.append({"name": name, "status": "FAIL", "error": traceback.format_exc()})

def login(page, role, username):
    page.locator(f'[data-login-role="{role}"]').click()
    page.locator("#login-id").fill(username)
    page.locator("#login-password").fill(username)
    page.locator("#login-password").press("Enter")

def open_student(page, student):
    page.locator(f'[data-action="open-student"][data-student="{student}"]').first.click()

def screenshot(page, name):
    page.wait_for_function("Array.from(document.querySelectorAll('#app img,#forest-world img')).every(i=>i.complete&&i.naturalWidth)")
    page.wait_for_timeout(220)
    page.evaluate("window.scrollTo(0,0)")
    page.screenshot(path=str(OUT / (name + ".png")))

def learning(page, token):
    for i in range(1, 11): page.get_by_test_id(f"unknown-W{i:04d}").click()
    page.get_by_test_id("start-plan").click()
    page.get_by_test_id("start-session").click()
    for i in range(10):
        q = page.evaluate("activityQuestion(currentSession().activities[currentSession().currentIndex])")
        page.get_by_test_id("option-" + q["correct_option_id"]).click()
        page.get_by_test_id("submit-answer").click()
        page.get_by_test_id("next").click()
    assert page.locator("[data-writing]").count() == 10
    for field in page.locator("[data-writing]").all(): field.fill(token + " 나의 단어 이야기를 썼어요.")
    page.get_by_test_id("submit-writing").click()

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path="/usr/bin/chromium", headless=True, args=["--no-sandbox"])
    context = browser.new_context(viewport={"width": 1280, "height": 960})
    def new_page():
        page = context.new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("response", lambda response: failed_requests.append(response.url) if response.status >= 400 else None)
        page.goto(URL)
        return page
    page = new_page()

    def entry():
        login(page, "teacher", "test2")
        assert page.locator("#app").get_attribute("data-view") == "teacher-roster"
        assert page.locator("[data-student-card]").count() == 3
        assert page.locator(".teacher-nav").count() == 0
        assert page.locator("#export-record").is_hidden() and page.locator("#reset").is_hidden()
        assert page.locator("#back").is_disabled()
        for design in ["forest", "city"]:
            page.locator("#design-" + design).click()
            screenshot(page, design + "-roster-desktop")
        return {"assignedStudents": 3, "studentSelectionRequired": True}
    check("Teacher login opens the assigned roster in both designs", entry)

    def two_students():
        page.locator("#logout").click()
        login(page, "student", "test1")
        learning(page, "JIWOO_ONLY")
        before_a = page.evaluate("JSON.stringify(state.sessions.regular)")
        other = new_page()
        login(other, "student", "test3")
        assert "김도윤" in other.locator("#account-context").inner_text()
        assert other.evaluate("allStats().writing") == 0
        learning(other, "DOYOON_ONLY")
        assert page.evaluate("JSON.stringify(state.sessions.regular)") == before_a
        page.reload()
        assert "이지우" in page.locator("#account-context").inner_text()
        assert "JIWOO_ONLY" in page.evaluate("JSON.stringify(state.sessions.regular)")
        assert "DOYOON_ONLY" not in page.evaluate("JSON.stringify(state.sessions.regular)")
        other.reload()
        assert other.evaluate("activeStudentId") == "student-doyoon"
        assert other.evaluate("allStats().writing") == 10
        other.close()
        page.locator("#logout").click()
        login(page, "teacher", "test2")
        for student in ["student-jiwoo", "student-doyoon"]:
            card = page.locator(f'[data-student-card="{student}"]')
            assert "작문 검토 대기 10건" in card.inner_text()
            assert card.locator('[role="progressbar"]').get_attribute("aria-valuenow") == "100"
        assert "20건" in page.locator(".metric-grid").inner_text()
        screenshot(page, "city-roster-with-progress")
        return {"parallelStudentTabs": 2, "objectiveSubmissions": 20, "writingSubmissions": 20}
    check("Two student tabs learn independently and populate the correct roster progress", two_students)

    def grading():
        open_student(page, "student-jiwoo")
        assert page.locator(".student-context h2").inner_text() == "이지우"
        page.locator('[data-action="teacher-page"][data-page="grading"]').click()
        assert "JIWOO_ONLY" in page.locator("#teacher-main").inner_text()
        assert "DOYOON_ONLY" not in page.locator("#teacher-main").inner_text()
        page.locator('[data-action="writing-judgment"][data-activity="regular-W1"][data-judgment="correct"]').click()
        page.locator('[data-grade-key="comment"][data-activity="regular-W1"]').fill("JIWOO_COMMENT_ONLY")
        page.locator('[data-action="confirm-grade"][data-activity="regular-W1"]').click()
        assert page.evaluate("resolveUnderstanding('W0001').group") == "known"
        page.locator('[data-action="teacher-page"][data-page="report"]').click()
        page.locator('[data-report-field="parentMessage"]').fill("JIWOO_PARENT_ONLY")
        page.locator('[data-report-field="internalMemo"]').fill("JIWOO_INTERNAL_PRIVATE")
        page.locator('[data-action="confirm-report"]').click()
        screenshot(page, "city-jiwoo-report")
        page.locator('[data-action="student-list"]').click()
        assert "작문 검토 대기 9건" in page.locator('[data-student-card="student-jiwoo"]').inner_text()
        open_student(page, "student-doyoon")
        page.locator('[data-action="teacher-page"][data-page="grading"]').click()
        assert "DOYOON_ONLY" in page.locator("#teacher-main").inner_text()
        assert "JIWOO_ONLY" not in page.locator("#teacher-main").inner_text()
        assert page.evaluate("allStats().graded") == 0
        assert page.evaluate("resolveUnderstanding('W0001').group") == "unknown"
        page.locator('[data-action="teacher-page"][data-page="report"]').click()
        assert page.locator('[data-report-field="parentMessage"]').input_value() == ""
        page.locator('[data-report-field="parentMessage"]').fill("DOYOON_PARENT_ONLY")
        page.locator('[data-report-field="internalMemo"]').fill("DOYOON_INTERNAL_PRIVATE")
        page.locator('[data-action="confirm-report"]').click()
        return {"firstStudentGraded": 1, "secondStudentGraded": 0, "studentReportsSeparate": True}
    check("Selected-student grading, automatic groups and parent messages remain separate", grading)

    def print_export():
        page.locator("#export-record").click()
        exported = json.loads(page.locator("#export-json").input_value())
        assert exported["studentId"] == "student-doyoon" and exported["fictionalStudent"] == "김도윤"
        assert "JIWOO_ONLY" not in json.dumps(exported)
        page.locator("#close-export").click()
        page.evaluate("prepareParentPrint()")
        page.emulate_media(media="print")
        text = page.locator("#print-area").inner_text()
        assert "김도윤의 어휘 학습 기록" in text and "DOYOON_PARENT_ONLY" in text
        assert "JIWOO_PARENT_ONLY" not in text and "DOYOON_INTERNAL_PRIVATE" not in text
        assert page.locator(".topbar").is_hidden() and page.locator("#forest-world").is_hidden()
        page.pdf(path=str(OUT / "doyoon-parent-report.pdf"), print_background=True)
        page.emulate_media(media="screen")
        page.locator('[data-action="student-list"]').click()
        assert page.locator("#export-json").input_value() == ""
        assert page.locator("#print-area").inner_html() == ""
        page.evaluate("prepareParentPrint()")
        assert page.locator("#print-area").inner_html() == ""
        return {"selectedStudentPrintAndExport": True, "browserPDFGenerated": True, "privateMemoExcluded": True}
    check("Selected-student JSON and print/PDF contain the correct name and clear on roster return", print_export)

    def filtering():
        page.locator("#roster-search").fill("도윤")
        assert page.locator("[data-student-card]").count() == 1
        page.locator("#roster-search").fill("없는학생")
        assert page.locator("[data-student-card]").count() == 0
        page.locator('[data-action="clear-roster-filter"]').click()
        assert page.locator("[data-student-card]").count() == 3
        page.locator("#roster-class").select_option("중등 어휘 B반")
        assert page.locator("[data-student-card]").count() == 1
        name = page.locator('.student-name[data-student="student-seoyeon"]')
        name.focus()
        name.press("Enter")
        assert page.locator(".student-context h2").inner_text() == "박서연"
        assert page.evaluate("allStats().writing") == 0
        page.locator("#back").click()
        assert page.locator("#roster-class").input_value() == "중등 어휘 B반"
        page.locator("#roster-class").select_option("all")
        return {"nameSearch": True, "classFilter": True, "emptyState": True, "keyboardNameSelection": True}
    check("Search, class filter, no-result recovery and keyboard student selection work", filtering)

    def responsive():
        for design in ["forest", "city"]:
            page.locator("#design-" + design).click()
            for width in [320, 360, 390, 768, 1280]:
                page.set_viewport_size({"width": width, "height": 960})
                assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
                for selector in ["#roster-search", "#roster-class", ".student-name", '.student-card button.primary']:
                    for el in page.locator(selector).all():
                        box = el.bounding_box()
                        assert box and box["height"] >= 44 and box["x"] >= 0 and box["x"] + box["width"] <= width + 1
                if width == 390: screenshot(page, design + "-roster-mobile")
            screenshot(page, design + "-roster-populated-desktop")
        return {"designs": 2, "viewports": [320, 360, 390, 768, 1280], "touchTargets": "at least 44px"}
    check("Both roster designs fit five viewport sizes with usable controls", responsive)

    def refresh_and_reset():
        page.set_viewport_size({"width": 1280, "height": 960})
        open_student(page, "student-jiwoo")
        page.locator('[data-action="teacher-page"][data-page="report"]').click()
        page.reload()
        assert page.locator("#roster-students").is_visible()
        open_student(page, "student-jiwoo")
        assert page.locator('[data-report-field="parentMessage"]').input_value() == "JIWOO_PARENT_ONLY"
        assert page.evaluate("allStats().graded") == 1
        a = page.evaluate("localStorage.getItem('vocabulary-pilot-flow-v2')")
        page.locator('[data-action="student-list"]').click()
        open_student(page, "student-doyoon")
        page.once("dialog", lambda dialog: dialog.accept())
        page.locator("#reset").click()
        assert page.evaluate("allStats().writing") == 0
        assert page.evaluate("localStorage.getItem('vocabulary-pilot-flow-v2')") == a
        page.locator('[data-action="student-list"]').click()
        open_student(page, "student-jiwoo")
        assert page.evaluate("allStats().writing") == 10
        assert page.locator('[data-report-field="parentMessage"]').input_value() == "JIWOO_PARENT_ONLY"
        return {"teacherReloadStartsAtRoster": True, "selectedStudentResetOnly": True, "otherStudentReportKept": True}
    check("Reload restores separate reports; reset clears only the selected student", refresh_and_reset)

    check("No script errors or failed images during roster and student management flows", lambda: {"scriptErrors": errors, "failedRequests": failed_requests} if not errors and not failed_requests else (_ for _ in ()).throw(AssertionError([errors, failed_requests])))
    browser.close()
server.shutdown()
result = {"method": "Real local Chromium; real UI actions, shared-origin parallel student tabs and browser print/PDF",
          "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
          "passed": sum(c["status"] == "PASS" for c in checks), "failed": sum(c["status"] == "FAIL" for c in checks),
          "limits": ["Fictional students and browser storage; no server authorization or cross-device synchronization.", "No physical devices or printers tested.", "Not deployed."], "checks": checks}
(OUT / "browser-results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"passed": result["passed"], "failed": result["failed"], "failed_checks": [c for c in checks if c["status"] == "FAIL"]}, ensure_ascii=False))
raise SystemExit(bool(result["failed"]))
