# Anti-patterns — Change / CD / design quality

## Change & evolution (CD)

- Intermediate merge leaves system non-releasable
- Risky incomplete behavior on by default (no flag / dark launch)
- Irreversible data loss without safeguards / rollback plan
- Huge PR mixing refactor with behavior change
- CI red or ignored; review substituting for automation
- Wrong config-vs-code deploy order that can outage
- System replacement without parallel-run / strangler / dual-write callout

## Design quality

- Needless complexity / speculative generality (gold plating) on hot or shared paths
- Shallow class explosion; leaking internals at boundaries
- Module API easy to misuse; unsafe defaults
- Net design-health degradation without a plan (Google standard)
- Temporal coupling (must-call-in-order APIs) without enforcement
- Feature envy / inappropriate intimacy across modules

## Process smells tied to change quality

- PR too large / multiple concerns without stacking plan
- “Tests follow-up” promise
- Empty description on non-trivial PR (missing why / risks / alternatives)

## Clean Code (blocking when on shared/hot paths)

- Dead / commented-out code masking intent in evolving modules
- Duplication that will diverge under parallel evolution of the same concern
