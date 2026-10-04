# 최신 커밋 저장·오류 처리 QA

대상: `0d7598638dac12c59e2cf7d0151b43a73f51c42a`의 독립 사본. 제품 파일은 수정하지 않았다. Node VM의 새 런타임, mock DOM·localStorage·OpenAI widgetState로 16개 항목을 실행했다. 10개 통과, 6개 문제 발견, 하네스 오류 0. 저장 손상 검사는 7개 하위 경우를 모두 실제 코드로 실행했다.

| 중요도 | 문제와 재현 방법 | 실제 결과 · 개선안 | 코드 위치 |
|---|---|---|---|
| P1 | 오래된 호스트 기록이 최신 입력을 덮음. 초고 수정 내용을 입력·저장한 뒤 이전 widgetState를 `openai:set_globals`로 전달 | 최신 `revisionDraft`가 이전 빈 값으로 바뀜. 기록 버전/수정 시각 비교, 필드별 병합, 충돌 복구 제공 | `prototype/pilot-flow.html:121` |
| P1 | 중첩된 손상 기록을 호환 v2로 수용. 진단 unknown=null, activity=null, currentIndex=-1, grades={}, 없는 selectedVersionId, 복습 response=null, 확정 부모 snapshot의 ratings 누락 중 하나를 저장 후 재시작 | 7종 모두 compatible=true 후 TypeError. 배열·개별 레코드·ID 참조·인덱스·부모 snapshot까지 검증하고 손상 데이터 보관 및 복구 화면 제공 | `prototype/pilot-flow.html:30`, `:31`; 실패 지점 `:53`, `:58`, `:66`, `:73`, `:91`, `:96`, `:113` |
| P2 | 잘못된 JSON이 원본 보관 없이 덮임. v2 키에 `{broken-json-with-original-data`를 넣고 재시작 | 오류 안내와 새 데모는 나오지만 첫 단어 카드 순서 저장이 원본을 덮음. 손상 원문을 별도 키로 보관하고 내려받기 제공 | `prototype/pilot-flow.html:32`, `:35`, `:53` |
| P2 | 호스트 동기 저장 실패 표시가 성공 표시로 덮임. setWidgetState가 동기 예외를 던지도록 한 뒤 저장 | 최종 문구가 `데모 기록 저장`. 로컬 저장과 호스트 저장 결과를 별도로 유지하고 실패 상태를 마지막에 표시 | `prototype/pilot-flow.html:35` |
| P2 | 저장된 ID가 교사 화면의 HTML 속성에 그대로 들어감. 정상 v2의 session.id를 `regular" onclick="globalThis.__qa_xss=1`로 바꾸고 작문 검토 화면 재시작 | 작문 판정 버튼에 실제 `onclick` 속성이 생성됨. 모든 속성 escape 및 허용 ID 검증. 일반 작문·코멘트는 escape되어 통과 | `prototype/pilot-flow.html:30`, `:96` |
| P3 | 일시 저장 실패 경고가 성공 이후에도 유지됨. 한번 QuotaExceededError를 발생시키고 다음 저장은 성공 | 저장된 값이 최신인데도 계속 `저장 실패`. 저장 성공 시 해당 경고를 해제 | `prototype/pilot-flow.html:35` |

위 중요도는 구현되어 있는 시제품 기능을 기준으로 한다. P1은 입력 손실 또는 화면 시작 불능, P2는 복구·오류 안내·저장 메타데이터 취약점, P3는 잘못 남은 상태 안내다. ID 속성 삽입은 저장/호스트 데이터 경로에서 확인했으며 일반 학생 입력으로 실행된 XSS라고 확대하지 않았다.

실제 검증하여 통과한 항목:

- 새 VM 런타임에서 미제출 객관 선택·힌트·랜덤 보기 순서·초고·미제출 수정본·교사 원문 버전·수동 애매함 조정 복구.
- 저장 읽기 거부, 용량 부족 예외에서 화면 진행 및 실패 안내; 메모리에 남은 값을 JSON으로 내보내기.
- v1 원문 유지·v2 초기화 후 v1 JSON 내보내기, v2 숫자 평가를 새 판정으로 임의 전환하지 않음.
- 초기 호스트 v2 우선 복구, 두 가지 이벤트 모양 지원, 동일 이벤트 25회 처리 시 호스트 재저장 루프 없음.
- 비동기 호스트 저장 거부의 안내, 작문·코멘트 HTML escape.
- 미확정 부모 메시지 제외, 확정 메시지 포함, 내부 메모 부모 HTML 제외.

미검증 또는 미구현:

- 실제 브라우저 localStorage/실제 용량 한도·파일 URL 환경·다중 탭 동기화·새로고침 조작은 미검증. 위 재시작은 VM 새 실행으로 검증했다.
- 실제 OpenAI 호스트 연결·네트워크 지연·클라우드 영속화는 미검증. 호스트 이벤트와 예외는 주입하여 검증했다.
- 실제 HTML `onclick` 실행은 미검증. 생성된 속성과 mock DOM의 파싱 결과만 확인했다.
- 서버 저장·학생 인증·교사 권한은 배너에 명시된 미구현 기능이다. 이번 버그 수에 넣지 않았다.

재실행: `node storage-errors-check.js /절대경로/prototype/pilot-flow.html`. 결과 및 실패 입력별 예외는 `storage-errors-results.json`, 발견만 추린 자료는 `findings.json`에 있다.
