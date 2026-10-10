"""Real local Chromium checks for design switching, persistence and draft safety."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import hashlib
import json
import traceback
from playwright.sync_api import sync_playwright

SOURCE = Path(__file__).resolve().parents[2] / "prototype/pilot-flow.html"
OUT = Path(__file__).resolve().parent / "designs"
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

def switch(page, design):
    page.locator("#design-" + design).click()
    assert page.locator("html").get_attribute("data-design") == design
    assert page.locator('.design-switch [aria-pressed="true"]').count() == 1

def saved(page):
    return page.evaluate("[JSON.stringify(state),localStorage.getItem('vocabulary-pilot-flow-v2')]")

def screenshot(page, name):
    page.wait_for_function("Array.from(document.querySelectorAll('#app img,#forest-world img')).every(i=>i.complete&&i.naturalWidth)")
    page.evaluate("window.scrollTo(0,0)")
    page.screenshot(path=str(OUT / (name + ".png")))

def login(page, role):
    page.locator(f'[data-login-role="{role}"]').click()
    value = "test1" if role == "student" else "test2"
    page.locator("#login-id").fill(value)
    page.locator("#login-password").fill(value)
    page.locator("#login-password").press("Enter")

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path="/usr/bin/chromium", headless=True, args=["--no-sandbox"])
    context = browser.new_context(viewport={"width": 1280, "height": 960})
    page = context.new_page()
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("response", lambda response: failed_requests.append(response.url) if response.status >= 400 else None)
    page.goto(URL)

    def initial_and_fields():
        assert page.locator("html").get_attribute("data-design") == "city"
        page.locator("#login-id").fill("test1")
        page.locator("#login-password").fill("test1")
        page.locator("#password-visibility").click()
        page.evaluate("window.qaLoginInput=document.getElementById('login-id')")
        before = saved(page)
        palettes = {}
        for design in ["forest", "city"]:
            switch(page, design)
            assert page.locator("#login-id").input_value() == "test1"
            assert page.locator("#login-password").input_value() == "test1"
            assert page.locator("#login-password").get_attribute("type") == "text"
            assert page.evaluate("qaLoginInput===document.getElementById('login-id')")
            assert saved(page) == before
            palettes[design] = page.locator(".login-submit").evaluate("e=>({radius:getComputedStyle(e).borderRadius,background:getComputedStyle(e).backgroundImage,color:getComputedStyle(e).color})")
            screenshot(page, design + "-login-desktop")
        assert palettes["forest"]["radius"] != palettes["city"]["radius"]
        assert palettes["city"]["background"].startswith("linear-gradient")
        return {"newVisitorDefault": "design 2", "formNodeAndInputKept": True, "palettes": palettes}
    check("Both designs change the UI while preserving typed credentials and password visibility", initial_and_fields)

    def responsive():
        for design in ["forest", "city"]:
            switch(page, design)
            for width in [320, 360, 390, 768, 1280]:
                page.set_viewport_size({"width": width, "height": 960})
                page.wait_for_function("document.querySelector('#forest-world img').complete")
                assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
                for button in page.locator(".topbar button:visible").all():
                    b = button.bounding_box()
                    assert b["x"] >= -1 and b["x"] + b["width"] <= width + 1
                for button in page.locator(".design-switch button").all(): assert button.bounding_box()["height"] >= 44
                expected = design + ("-world-mobile.webp" if width <= 800 else "-world.webp")
                page.wait_for_function("document.querySelector('#world-image').currentSrc.endsWith(" + json.dumps(expected) + ")")
                assert page.locator("#forest-world").evaluate("e=>getComputedStyle(e).pointerEvents") == "none"
                if width == 390: screenshot(page, design + "-login-mobile")
        page.set_viewport_size({"width": 1280, "height": 960})
        return {"widths": [320, 360, 390, 768, 1280], "bothResponsivePictures": True, "selectorTargetsAtLeast44px": True}
    check("Both designs and the header fit mobile/tablet/desktop with responsive scene assets", responsive)

    def keyboard_and_reload():
        page.locator("#design-forest").focus()
        page.keyboard.press("Enter")
        assert page.locator("#design-forest").evaluate("e=>e===document.activeElement")
        assert page.locator("html").get_attribute("data-design") == "forest"
        page.reload()
        assert page.locator("html").get_attribute("data-design") == "forest"
        switch(page, "city")
        page.reload()
        assert page.locator("html").get_attribute("data-design") == "city"
        return {"keyboardActivation": True, "focusKept": True, "bothPreferencesPersist": True}
    check("Design selection is keyboard accessible and persists across reload", keyboard_and_reload)

    def student_drafts():
        login(page, "student")
        page.locator('[data-action="fill-example"]').click()
        page.get_by_test_id("start-plan").click()
        page.get_by_test_id("start-session").click()
        first = page.locator(".answer").first
        first.click()
        before = saved(page)
        choice = page.locator(".answer.selected").get_attribute("data-option")
        for design in ["forest", "city"]:
            switch(page, design)
            assert saved(page) == before
            assert page.locator(".answer.selected").get_attribute("data-option") == choice
        for index in range(10):
            q = page.evaluate("studyQuestion(currentSession().activities[currentSession().currentIndex],currentSession().responses[currentSession().activities[currentSession().currentIndex].id])")
            page.get_by_test_id("option-" + q["correct_option_id"]).click()
            page.get_by_test_id("submit-answer").click()
            page.get_by_test_id("next").click()
        fields = page.locator("[data-writing]")
        fields.first.fill("내 생각을 담아 단어를 사용한 가상 작문입니다.")
        page.evaluate("window.qaWritingNode=document.querySelector('[data-writing]')")
        before = saved(page)
        for design in ["forest", "city"]:
            switch(page, design)
            assert saved(page) == before
            assert fields.first.input_value().startswith("내 생각")
            assert page.evaluate("qaWritingNode===document.querySelector('[data-writing]')")
            screenshot(page, design + "-writing-desktop")
        for field in fields.all(): field.fill("배운 단어를 사용하는 가상 학생의 문장입니다.")
        page.get_by_test_id("submit-writing").click()
        page.locator("#logout").click()
        assert page.locator("html").get_attribute("data-design") == "city"
        return {"pendingAnswerKept": True, "draftNodeAndTextKept": True, "objectiveSubmissions": 10, "writingSubmissions": 10, "logoutKeepsDesign": True}
    check("Changing designs preserves selected answers, writing drafts, and submitted learning", student_drafts)

    def teacher_drafts_and_charts():
        login(page, "teacher")
        page.locator('[data-action="teacher-page"][data-page="grading"]').click()
        activity = page.locator('[data-action="writing-judgment"]').first.get_attribute("data-activity")
        page.locator(f'[data-action="writing-judgment"][data-activity="{activity}"][data-judgment="correct"]').click()
        comment = page.locator(f'[data-grade-key="comment"][data-activity="{activity}"]')
        comment.fill("THEME_REVIEW_COMMENT 뜻에 맞게 썼어요.")
        before = saved(page)
        for design in ["forest", "city"]:
            switch(page, design)
            assert saved(page) == before
            assert comment.input_value().startswith("THEME_REVIEW_COMMENT")
            assert page.locator(f'[data-action="writing-judgment"][data-activity="{activity}"][aria-pressed="true"]').count() == 1
        page.locator(f'[data-action="confirm-grade"][data-activity="{activity}"]').click()
        page.locator('[data-action="teacher-page"][data-page="report"]').click()
        page.locator('[data-report-field="parentMessage"]').fill("THEME_PARENT_MESSAGE 꾸준히 탐험하고 있어요.")
        page.locator('[data-report-field="internalMemo"]').fill("THEME_INTERNAL_PRIVATE")
        before = saved(page)
        values, colors = [], []
        for design in ["forest", "city"]:
            switch(page, design)
            assert saved(page) == before
            assert page.locator('[data-report-field="parentMessage"]').input_value().startswith("THEME_PARENT_MESSAGE")
            values.append(page.locator(".assessment-chart").first.inner_text())
            colors.append(page.locator('.donut-svg [data-chart-category="correct"]').first.evaluate("e=>getComputedStyle(e).fill"))
            screenshot(page, design + "-teacher-report-desktop")
        assert values[0] == values[1] and colors[0] != colors[1]
        page.locator('[data-action="confirm-report"]').click()
        page.reload()
        assert page.locator('[data-report-field="parentMessage"]').input_value().startswith("THEME_PARENT_MESSAGE")
        assert page.locator("html").get_attribute("data-design") == "city"
        return {"gradeDraftAndCommentKept": True, "reportDraftKept": True, "chartDataUnchanged": True, "chartColorsChange": colors, "reloadKeepsReportAndDesign": True}
    check("Teacher grading/report drafts persist and chart data stays identical when colors change", teacher_drafts_and_charts)

    def independent_preferences():
        page.locator("#forest-motion-toggle").click()
        assert page.locator("#forest-world").get_attribute("data-motion") == "paused"
        for design in ["forest", "city"]:
            switch(page, design)
            assert page.locator("#forest-world").get_attribute("data-motion") == "paused"
        other = context.new_page()
        other.goto(URL)
        before = saved(page)
        switch(other, "forest")
        page.wait_for_function("document.documentElement.getAttribute('data-design')==='forest'")
        assert saved(page) == before
        other.close()
        page.emulate_media(reduced_motion="reduce")
        switch(page, "city")
        assert page.locator(".city-drone").evaluate("e=>getComputedStyle(e).animationName") == "none"
        assert page.locator("#forest-motion-toggle").is_disabled()
        page.emulate_media(reduced_motion="no-preference")
        assert page.locator("#forest-world").get_attribute("data-motion") == "paused"
        return {"motionPreferenceIndependent": True, "crossTabDesignSync": True, "reducedMotionHonoredAcrossDesigns": True}
    check("Motion settings stay independent, OS reduction is honored, and other tabs synchronize design", independent_preferences)

    def storage_errors_and_reset():
        page.evaluate("()=>{window.qaOriginalSet=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(k==='vocabulary-design-v1')throw new Error('QuotaExceededError');return qaOriginalSet.call(this,k,v)}}")
        before = saved(page)
        switch(page, "forest")
        assert saved(page) == before
        assert page.locator("#design-status").is_visible()
        page.evaluate("()=>{Storage.prototype.setItem=qaOriginalSet}")
        switch(page, "city")
        assert not page.locator("#design-status").is_visible()
        page.on("dialog", lambda d: d.accept())
        page.locator("#reset").click()
        assert page.locator("html").get_attribute("data-design") == "city"
        assert page.evaluate("localStorage.getItem('vocabulary-design-v1')") == "city"
        for init in ["localStorage.setItem('vocabulary-design-v1','../../invalid')", "const original=Storage.prototype.getItem;Storage.prototype.getItem=function(k){if(k==='vocabulary-design-v1')throw new Error('SecurityError');return original.call(this,k)}"]:
            isolated = browser.new_context()
            isolated.add_init_script(init)
            temp = isolated.new_page()
            temp.goto(URL)
            assert temp.locator("html").get_attribute("data-design") == "city"
            switch(temp, "forest")
            isolated.close()
        return {"storageFailureKeepsCurrentChoiceAndLearning": True, "warningRecoversAfterSuccessfulSave": True, "invalidOrBlockedReadFallsBack": True, "learningResetKeepsDesign": True}
    check("Storage failures recover safely, invalid preferences are ignored, and learning reset retains design", storage_errors_and_reset)
    check("No uncaught errors or broken assets during design switching", lambda: {"errors": errors, "failedRequests": failed_requests} if not errors and not failed_requests else (_ for _ in ()).throw(AssertionError([errors,failed_requests])))
    browser.close()
server.shutdown()
result = {"method":"Real local Chromium through Playwright", "html_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest(), "passed":sum(c["status"]=="PASS" for c in checks), "failed":sum(c["status"]=="FAIL" for c in checks), "checks":checks, "deploymentPerformed":False}
(OUT / "browser-results.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
print(json.dumps({"passed":result["passed"],"failed":result["failed"],"failures":[c for c in checks if c["status"]=="FAIL"]},ensure_ascii=False))
raise SystemExit(bool(result["failed"]))
