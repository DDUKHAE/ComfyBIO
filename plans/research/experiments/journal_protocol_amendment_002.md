# Protocol Amendment COMFYBIO-JOURNAL-001-A002

- 날짜: 2026-06-22
- 유형: 목표 저널 변경, 연구 분석 기준 변경 없음
- Held-out 결과 확인 여부: 아니요
- 승인 상태: 사용자 요청에 따라 반영

## 변경 이유

기존 목표인 Bioinformatics Advances보다 Impact Factor가 높은 저널을 우선 목표로 설정하기 위해 공식 scope와 최신 공개 지표를 비교했다.

## 변경 전

- 1차 목표: Bioinformatics Advances, Original Article / Software
- 2024 Impact Factor: 2.8
- Scope SHA-256: `aeaa0951fec09e70c64d22ff6b8b00aafb0c21dcadd6adc7c9f391fa90b7da56`
- Protocol SHA-256: `6e575e2fe6cf588118b793581c01ae40eff645557b2038cd9cd822d760b3ec68`

## 변경 후

1. 1차 목표: Briefings in Bioinformatics — new methods 중심 original research / case study
2. 2차 목표: Bioinformatics — Original Paper
3. 3차 fallback: Bioinformatics Advances — Original Article / Software

공식 공개 지표:

- Briefings in Bioinformatics: 2024 IF 7.7, 5-Year IF 8.7, 2025 CiteScore 13.6
- Bioinformatics: 2024 IF 5.4, 5-Year IF 7.1, 2025 CiteScore 11.1
- Bioinformatics Advances: 2024 IF 2.8

새 freeze hash:

- Scope SHA-256: `e3465dfa4777bdd3500df2b3e5e9da2f8b5896b71c340fa0c303eeb1b477fb49`
- Protocol SHA-256: `87339967d81827cdd7ed76af2a4291a2676208ff060e372f6244aa607902b4dc`

## 선택 근거

BIB는 공식 scope에서 review뿐 아니라 new methods, case studies, analytical tools 및 AI/ML applications를 포함한다. 현재 연구가 120개 held-out query, 다중 workflow family, 실제 실행, 전문가 평가와 재현성 package를 완결하면 BIB의 method/case-study 범위에 도전할 수 있다.

Bioinformatics는 실제 biological data와 state-of-the-art 비교를 요구하는 Original Paper가 현재 설계와 직접적으로 잘 맞으므로 2차 목표로 지정한다.

## 영향 평가

다음 항목은 변경하지 않았다.

- 연구 가설과 claim 판정 규칙
- Primary/secondary endpoint
- 120개 표본 수와 난이도 분포
- Workflow family
- 실험 arm, 반복 횟수 및 randomization
- 제외 및 retry 정책
- 통계 분석
- 전문가 평가와 blinding
- Quality gate

저널 변경은 연구 결과를 확인하기 전에 이루어졌으며 benchmark 실행이나 분석 결과에 영향을 주지 않는다.

## 추가 실행 요건

BIB/Bioinformatics 수준을 목표로 다음을 submission-readiness gate에서 강화한다.

- 실제 biological data fixture 사용
- 비자명한 다단계 workflow 실행 증거
- 관련 state-of-the-art method와의 비교 가능성 검토
- 단순 software integration을 넘어서는 일반화 가능한 방법론 기여
- 넓은 computational biology 독자층에 유용한 실패 분석과 실무 지침

## 공식 출처

- [Briefings in Bioinformatics 소개 및 지표](https://academic.oup.com/bib/pages/About)
- [Bioinformatics 저자 지침](https://academic.oup.com/bioinformatics/pages/General_Instructions)
- [Bioinformatics 소개 및 지표](https://academic.oup.com/bioinformatics/pages/About)
- [Bioinformatics Advances 저자 지침](https://academic.oup.com/bioinformaticsadvances/pages/instructions-to-authors)
