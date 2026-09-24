# How to train

The objective is a repeatable diagnostic method that transfers to unfamiliar incidents. Speed is secondary to using evidence and making a safe, durable change.

## One session

1. **Recall (2 minutes).** Before using notes, write your first three investigative steps and what each result would tell you.
2. **Investigate (20–45 minutes).** Read problem.md. Establish the symptom and scope; collect evidence; state a hypothesis; choose a command that can disprove it. Change one variable at a time.
3. **Get feedback.** Run verify when you expect recovery. If stuck without a new hypothesis for about 15 minutes, request hint 1; after another 10 minutes try hint 2. The timings are adjustable guardrails, not research-derived thresholds. Record hints without treating them as failure.
4. **Test durability.** Run the host command `./labctl durable N`. Explain why the fix should survive a restart before checking it.
5. **Recall again (3 minutes).** Close the logs and notes. Explain the cause, the evidence that distinguished it from another hypothesis, and one production prevention measure. Compare with your evidence afterward.

Avoid writing an essay after every command. A short debrief is a design choice to keep most time on investigation and feedback.

## Suggested schedule

| Session | Work |
|---|---|
| Day 1 | Incident 1 |
| Day 2 | Recall incident 1 from memory, then incident 2 |
| Day 3 | Incident 3 |
| Day 4 | Reset and retry incident 1 without notes; then incident 4 if time permits |
| Day 5 | Incident 5 |
| Day 8 | Reset and retry 3, then 2, without knowing the cause from notes |
| Day 12 | Retry 5 and 4; compare evidence and hints with the first attempt |
| Day 20 | Choose one incident randomly; diagnose before editing anything |

These intervals are practical defaults, not a uniquely optimal schedule. Space further apart after confident, unaided success; shorten the interval if you cannot explain the cause. Start sequentially to build confidence, then mix incident types so you must choose an investigative method.

Repeating the same fault can become solution memorization. On a revisit, predict the output of three diagnostic commands before running them, and explain an alternative cause that the evidence rules out. For stronger transfer after these five, ask for new incidents with different underlying faults; merely changing ports would offer limited additional practice.

## Evaluate growth

Score each dimension 0 (not yet), 1 (with help), or 2 (independently): isolate the failing layer; support a hypothesis with evidence; make a minimal safe fix; verify representative behavior after restart; explain prevention from memory. Record time and hints as context, not as a competition. A passing verifier alone does not establish mastery.

## Research behind the design

- Carnegie Mellon’s [retrieval practice guidance](https://www.cmu.edu/teaching/resources/instructionalstrategies/activelearningstrategies/retrievalpractice/index.html) describes recalling information and receiving corrective feedback. Here that becomes predicting diagnostics and giving a closed-notes debrief followed by verification.
- The Learning Scientists explain [spaced practice](https://www.learningscientists.org/learning-scientists-podcast/2017/10/4/episode-4-spaced-practice): revisit learning across separated sessions. Here that becomes reset-and-retry sessions over several weeks.
- Their [interleaving guidance](https://www.learningscientists.org/blog/2016/8/11-1) supports mixing problem types and combining it with retrieval. Here that becomes mixed-order revisits after an initial ordered pass.
- Carnegie Mellon’s [learning principles](https://www.cmu.edu/teaching/principles/learning.html) emphasize goal-directed practice with targeted feedback. Here that becomes explicit recovery criteria, graduated hints, and checks of real behavior.

These sources concern learning broadly; applying them to this DevOps lab is an informed design choice, not a claim that this exact five-VM curriculum has been experimentally validated.

## Network extension

Complete labs 6–8 over separate sessions. Before changing anything, state the observed symptom, the affected client and a hypothesis you can test. Predict one result, collect evidence, then update the hypothesis. After recovery, check reboot persistence and explain why the change was sufficient while preserving the required boundaries.

Revisit one lab after several days and another after a week. Mix them with an earlier incident so you must select your own diagnostic approach. If you remember the edit immediately, explain the evidence first; remembered fixes alone do not demonstrate transfer to a new incident.
