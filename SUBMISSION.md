# Submission

Fork URL: <!-- paste the URL of your fork here -->

## Files to commit

- [ ] `rolling/`, `bluegreen/` and `canary/` with your manifests
- [ ] `notes.md` with the numbers you measured (optional)

## Questions

Answer in your own words. Where a question asks for output, paste it in a code block.

### Q1. Paste your rolling-update strategy and say what `maxSurge` and `maxUnavailable` mean with 4 replicas. Why must `maxUnavailable` be 0 here, and why does it still need a readiness probe to be safe? What does a rolling update do if the new pods never become Ready?

**Your answer:**

<!-- replace this line with your answer -->

### Q2. During the rollout the client saw both versions. For how many seconds, and is that a problem? Name one kind of change (a database schema, an API field) for which two versions running together is NOT safe.

**Your answer:**

<!-- replace this line with your answer -->

### Q3. Paste the one command that switches blue/green and the result seen from the client. Why is the switch instant, and why does the old (blue) version stay running afterwards? What does that cost, and what does it buy you?

**Your answer:**

<!-- replace this line with your answer -->

### Q4. Paste the share of version 2 you measured in 200 requests with a 9:1 canary. Why is it not exactly 10%? How would you send exactly 10% (hint: a service mesh or an ingress controller weights traffic by request, replicas only by pod count)?

**Your answer:**

<!-- replace this line with your answer -->

### Q5. Roll back each strategy: rolling (`rollout undo`), blue/green (switch the selector), canary (scale it to zero). Which is fastest, which is the only one that needs a rebuild of state, and which would you use for a database migration?

**Your answer:**

<!-- replace this line with your answer -->

### Q6. Which strategy would you choose for: a typo fix, a new payment provider, a change nobody has tested at full load? Give a one-line reason each.

**Your answer:**

<!-- replace this line with your answer -->

### Q7. Paste the output of `./verify.sh`. It must end with **ALL CHECKS PASSED**.

**Your answer:**

<!-- replace this line with your answer -->

### Q8. **Tear down.** Paste the output of `./verify-teardown.sh`. It must end with **TEARDOWN VERIFIED**.

**Your answer:**

<!-- replace this line with your answer -->
