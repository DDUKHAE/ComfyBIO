# Operational Status

## Scope

이 문서는 2026-06-16 기준 `ComfyBIO Biopython`의 하이브리드 워크플로우 생성 계층에 대한 현재 운영 상태를 정리한다.

## Implemented

- hybrid workflow generation pipeline
- canonical template registry and template-guided local repair
- deterministic normalization and equivalence scoring
- workflow history metadata persistence
- experiment batch runner and markdown reporting
- provider readiness CLI
- structured benchmark query sets

## Functionally Implemented but Operationally Conditional

### Codex

- code path: available
- account compatibility issue: `codex-mini-latest` 대신 `gpt-5.5` 사용 필요
- current evidence: live smoke comparison에서 `gpt-5.5` 기준 generation 성공
- reference:
  - [2026-06-15-provider-smoke-comparison.md](/home/ydj/main/ComfyBIO_biopython/docs/superpowers/experiments/2026-06-15-provider-smoke-comparison.md)
  - [2026-06-15-codex-failure-diagnostic.md](/home/ydj/main/ComfyBIO_biopython/docs/superpowers/experiments/2026-06-15-codex-failure-diagnostic.md)

### Claude

- code path: available
- auth status: logged in
- operational issue: session limit 때문에 live generation 실패 가능
- current evidence: provider smoke comparison에서 모든 query/mode가 session limit 오류로 실패
- reference:
  - [2026-06-15-provider-smoke-comparison.md](/home/ydj/main/ComfyBIO_biopython/docs/superpowers/experiments/2026-06-15-provider-smoke-comparison.md)

### Gemini

- code path: available
- operational issue: 현재 환경에서 미설치/미준비
- current evidence: readiness artifact에서 not ready
- reference:
  - [2026-06-15-provider-readiness.md](/home/ydj/main/ComfyBIO_biopython/docs/superpowers/experiments/2026-06-15-provider-readiness.md)

## Authoritative Interpretation Order

provider 상태를 판단할 때는 아래 순서를 우선한다.

1. live smoke comparison report
2. provider-specific diagnostic report
3. readiness report

이 순서를 쓰는 이유는 readiness는 설치/인증 상태를 잘 보여주지만, 실제 generation quota나 session limit까지 완전히 대변하지 않기 때문이다. 또한 현재 저장된 readiness artifact는 rollout 중간 산출물을 포함하므로, 운영 판단의 1차 근거로 쓰지 않는다.

## Remaining Work

남은 일은 현재 대부분 코드 변경보다 운영 환경에 가깝다.

1. `claude` quota/session limit 해소 후 smoke benchmark 재실행
2. `gemini` 설치 및 로그인 후 smoke benchmark 편입
3. 필요 시 provider readiness artifact를 최신 probe 결과로 재생성

## Conclusion

현재 저장소는 `연구용 하이브리드 워크플로우 생성 시스템`으로서 코드 구현은 상당 부분 완료된 상태다. 다만 multi-provider 운영 완결성은 외부 provider 상태에 의해 아직 제한된다.
