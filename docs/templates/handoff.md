# Handoff: <agent> | <Project> r<NN> | <date time>

- **Stopped because:** <ceiling reached | usage limit | blocked on X | done>.
- **Tool calls used (harness count):** <n>.

## Done (verified)
- <ID>: <what changed>, <before → after>, <gate result>.

## Not done
- <ID>: <current state>, <why>, <what to try next>.
  If an approach already failed twice, write "stop: two failures" and do not repeat it.

## Files
- **Current preview:** <path>. Passes the hard gates: <yes / no: which one fails>.
- **Changed modules:** <paths>.
- **Build command:** `<cmd>`. Last build time: <s>.

## Next step for a fresh agent
1. <first action>
2. <second action>
