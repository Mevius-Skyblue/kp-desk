"""P2 bond math engine (config/p2.yaml). Pure functions, no database or network access.

Modules:
  daycount   날짜 계산: 월 더하기, 30/360, Act/Act(ICMA) 기간 비율, 결제일(T+n)
  pricing    고정금리 채권: 현금흐름 일정, 가격 <-> 수익률, 경과이자, 듀레이션·볼록성·DV01
  interp     보간: 선형(기본), 단조 3차(Fritsch-Carlson, 민감도)
  curve      재무부 par 커브 -> 제로 커브 부트스트랩, G-spread, Z-spread, 스프레드 듀레이션
  analytics  deals -> bond_analytics 표 (python -m src.bond.analytics)
"""
