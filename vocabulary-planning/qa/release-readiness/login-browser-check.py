"""Real Chromium checks on a local HTTP server. This script never deploys."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import hashlib
import json
import traceback

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "login"
OUT.mkdir(exist_ok=True)
SOURCE = ROOT / "prototype/pilot-flow.html"
AUTH_KEY = "vocabulary-demo-login-v1"
checks, errors, contexts = [], [], []


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(SOURCE.parent)))
Thread(target=server.serve_forever, daemon=True).start()
URL = f"http://127.0.0.1:{server.server_port}/pilot-flow.html"


def new_page(browser, width=1280):
    context = browser.new_context(viewport={"width": width, "height": 900})
    contexts.append(context)
    page = context.new_page()
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(URL)
    return page


def credentials(page, role, username=None, password=None, enter=False):
    page.locator(f'[data-login-role="{role}"]').click()
    value = "test 2" if role == "teacher" else "test 1"
    page.locator("#login-id").fill(username if username is not None else value)
    page.locator("#login-password").fill(password if password is not None else value)
    if enter:
        page.locator("#login-password").press("Enter")
    else:
        page.locator('#login-form button[type="submit"]').click()


def check(name, fn):
    try:
        details = fn() or {}
        checks.append({"name": name, "status": "PASS", "details": details})
    except Exception:
        checks.append({"name": name, "status": "FAIL", "error": traceback.format_exc()})
    finally:
        while contexts:
            contexts.pop().close()


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(executable_path="/usr/bin/chromium", headless=True, args=["--no-sandbox"])

    def initial():
        page = new_page(browser)
        assert page.locator("#login-form").is_visible()
        assert page.locator("[data-login-role]").count() == 2
        assert not page.locator("#account-toolbar").is_visible()
        assert not page.locator(".steps").count()
        assert not page.locator('input[type="email"]').count()
        page.screenshot(path=str(OUT / "student-login-desktop.png"), full_page=True)
    check("Signed-out start shows student login and no learning or teacher menu", initial)

    def invalid():
        page = new_page(browser)
        page.locator('#login-form button[type="submit"]').click()
        assert "모두 입력" in page.locator("#login-error").inner_text()
        for role, username, password in [("student", "test 1", "wrong"), ("student", "test 2", "test 2"),
                                          ("teacher", "test 1", "test 1"), ("teacher", "test 2", "wrong"),
                                          ("student", "test1", "test 1"), ("student", "test 1", "test 1 ")]:
            credentials(page, role, username, password)
            assert page.locator("#login-form").is_visible()
            assert "확인" in page.locator("#login-error").inner_text()
            assert page.locator("#login-password").input_value() == ""
        return {"invalidCases": 6, "passwordSpacesAreSignificant": True}
    check("Empty, wrong, cross-role and space-sensitive credentials cannot log in", invalid)

    def switching():
        page = new_page(browser)
        page.locator("#login-id").fill("test 1")
        page.locator("#login-password").fill("private-entry")
        page.locator("#password-visibility").click()
        assert page.locator("#login-password").get_attribute("type") == "text"
        assert page.locator("#login-password").input_value() == "private-entry"
        page.locator('[data-login-role="teacher"]').click()
        assert page.locator("#login-id").input_value() == ""
        assert page.locator("#login-password").input_value() == ""
        assert page.locator("#login-password").get_attribute("type") == "password"
        assert page.locator('[data-login-role="teacher"]').get_attribute("aria-pressed") == "true"
        page.screenshot(path=str(OUT / "teacher-login-desktop.png"), full_page=True)
    check("Role switching clears fields; password visibility keeps the entered value", switching)

    def student():
        page = new_page(browser)
        credentials(page, "student", " test 1 ", "test 1", enter=True)
        assert page.locator("#account-badge").inner_text() == "학생 · test 1"
        assert page.get_by_test_id("unknown-W0001").is_visible()
        assert not page.locator(".teacher-nav").count()
        assert not page.locator("#export-record").is_visible()
        assert not page.locator("#reset").is_visible()
        page.evaluate("state.role='teacher';render();teacherPage('report');prepareParentPrint()")
        assert not page.locator(".teacher-nav").count()
        assert page.evaluate("state.role") == "student"
        assert page.locator("#print-area").inner_html() == ""
        page.get_by_test_id("unknown-W0001").click()
        page.reload()
        assert page.locator("#account-badge").inner_text() == "학생 · test 1"
        assert page.evaluate("state.diagnostic.unknown.W0001") is True
        marker = page.evaluate(f"JSON.parse(sessionStorage.getItem('{AUTH_KEY}'))")
        assert set(marker) == {"version", "role", "username", "expiresAt"}
        return {"keyboardSubmit": True, "refreshKeepsLoginAndDiagnosis": True, "passwordStored": False}
    check("Student login enters diagnosis, resumes on reload and cannot open teacher UI", student)

    def teacher():
        page = new_page(browser)
        credentials(page, "teacher")
        assert page.locator("#account-badge").inner_text() == "교사 · test 2"
        assert page.locator(".teacher-nav").is_visible()
        page.locator('[data-action="teacher-page"][data-page="report"]').click()
        page.locator('[data-report-field="parentMessage"]').fill("부모님께 전하는 테스트 메시지")
        page.locator('[data-report-field="internalMemo"]').fill("LOGIN_PRIVATE_MEMO")
        page.locator('[data-action="confirm-report"]').click()
        page.evaluate("prepareParentPrint()")
        assert "부모님께 전하는 테스트 메시지" in page.locator("#print-area").inner_html()
        assert "LOGIN_PRIVATE_MEMO" not in page.locator("#print-area").inner_html()
        page.locator("#export-record").click()
        assert "LOGIN_PRIVATE_MEMO" in page.locator("#export-json").input_value()
        page.locator("#logout").click()
        assert page.locator("#login-form").is_visible()
        assert page.locator("#export-panel").is_hidden()
        assert page.locator("#export-json").input_value() == ""
        assert page.locator("#print-area").inner_html() == ""
        assert page.evaluate(f"sessionStorage.getItem('{AUTH_KEY}')") is None
        page.reload()
        assert page.locator("#login-form").is_visible()
        assert not page.locator(".teacher-nav").count()
        credentials(page, "teacher")
        assert page.locator('[data-report-field="parentMessage"]').input_value() == "부모님께 전하는 테스트 메시지"
    check("Teacher login edits reports; logout clears panels and keeps saved report text", teacher)

    def invalid_sessions():
        page = new_page(browser)
        credentials(page, "teacher")
        page.locator("#logout").click()
        for marker in ["{broken", json.dumps({"version": 1, "role": "admin", "username": "test 2", "expiresAt": 9999999999999}),
                       json.dumps({"version": 1, "role": "teacher", "username": "test 2", "expiresAt": 0})]:
            page.evaluate("([key,value])=>sessionStorage.setItem(key,value)", [AUTH_KEY, marker])
            page.reload()
            assert page.locator("#login-form").is_visible()
            assert not page.locator(".teacher-nav").count()
        page.evaluate("state.role='teacher';state.teacherScreen='report';persist()")
        page.reload()
        assert page.locator("#login-form").is_visible()
        assert page.locator("#storage-status").inner_text() == ""
    check("Broken, unknown and expired sessions and old saved teacher role start signed out", invalid_sessions)

    def full_learning():
        page = new_page(browser, 390)
        credentials(page, "student")
        for i in range(1, 11):
            page.get_by_test_id(f"unknown-W{i:04d}").click()
        page.get_by_test_id("start-plan").click()
        page.get_by_test_id("start-session").click()
        titles = page.evaluate("WORDS.map(w=>titleWord(w.id))")
        for i in range(10):
            q = page.evaluate("studyQuestion(currentSession().activities[currentSession().currentIndex],currentSession().responses[currentSession().activities[currentSession().currentIndex].id])")
            visible = page.locator(".answer > span:last-child").all_text_contents()
            assert len(visible) == len(set(visible)) == 4 and set(visible).issubset(titles)
            choice = next(o["id"] for o in q["options"] if o["id"] != q["correct_option_id"]) if i == 0 else q["correct_option_id"]
            page.get_by_test_id("option-" + choice).click()
            if i == 3:
                page.reload()
                assert page.get_by_test_id("option-" + choice).get_attribute("aria-pressed") == "true"
            page.get_by_test_id("submit-answer").click()
            page.get_by_test_id("next").click()
        assert page.locator("[data-writing]").count() == 10
        for field in page.locator("[data-writing]").all():
            field.fill("배운 단어로 상황에 알맞은 문장을 쓰는 테스트입니다.")
        page.locator('[data-action="submit-writing"]').click()
        before = page.evaluate("JSON.stringify(state.sessions.regular)")
        page.locator("#logout").click()
        credentials(page, "teacher")
        assert page.evaluate("JSON.stringify(state.sessions.regular)") == before
        page.locator('[data-action="teacher-page"][data-page="grading"]').click()
        activities = page.evaluate("state.sessions.regular.writingActivities")
        for activity in activities:
            page.locator(f'[data-action="writing-judgment"][data-activity="{activity["id"]}"][data-judgment="correct"]').click()
            page.locator(f'[data-action="confirm-grade"][data-activity="{activity["id"]}"]').click()
        assert page.evaluate("allStats().graded") == 10
        page.locator("#logout").click()
        credentials(page, "student")
        assert page.evaluate("allStats().graded") == 10
        return {"objectiveAnswers": 10, "writingSubmissions": 10, "teacherGrades": 10,
                "diagnosisOnlyChoices": True, "viewport": "390×900"}
    check("Real student learning, pending reload, ten writings and teacher grading survive account changes", full_learning)

    def responsive():
        measurements = []
        for width in [360, 390, 768, 1280]:
            page = new_page(browser, width)
            for role in ["student", "teacher"]:
                page.locator(f'[data-login-role="{role}"]').click()
                assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
                for selector in ["#login-id", "#login-password", '#login-form button[type="submit"]']:
                    box = page.locator(selector).bounding_box()
                    assert box and box["height"] >= 44 and box["x"] >= 0 and box["x"] + box["width"] <= width + 1
                measurements.append({"width": width, "role": role, "horizontalOverflow": False})
            if width == 390:
                page.screenshot(path=str(OUT / "teacher-login-mobile.png"), full_page=True)
        return {"viewports": measurements, "physicalDevice": "not tested"}
    check("Student and teacher login layouts fit 360, 390, 768 and 1280 pixel viewports", responsive)
    check("Browser completes login and learning flows with no uncaught JavaScript errors", lambda: {} if not errors else (_ for _ in ()).throw(AssertionError(errors)))
    browser.close()
server.shutdown()

result = {"method": "Real local Chromium via Playwright; isolated browser contexts and local HTTP only",
          "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
          "passed": sum(c["status"] == "PASS" for c in checks), "failed": sum(c["status"] == "FAIL" for c in checks),
          "deployment": "NOT RUN: user requested deployment only on explicit instruction",
          "limits": ["Fixed front-end test accounts; no server authentication or authorization.",
                     "Responsive browser viewports, not physical devices; actual printing deferred."], "checks": checks}
(OUT / "browser-results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"passed": result["passed"], "failed": result["failed"],
                  "failed_checks": [c for c in checks if c["status"] == "FAIL"]}, ensure_ascii=False))
raise SystemExit(bool(result["failed"]))
