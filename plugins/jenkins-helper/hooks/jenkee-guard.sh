#!/bin/bash
# jenkee-guard.sh
# PreToolUse hook: force a confirmation on destructive jenkee/jks commands,
# reminding the caller which Jenkins profile/site is currently active.
input=$(cat)
cmd=$(echo "$input" | jq -r '.tool_input.command // empty')

if echo "$cmd" | grep -Eq '(^|[[:space:]])(jenkee|jks)[[:space:]]+(delete-job|delete-builds|disable-job|enable-job|groovy)([[:space:]]|$)'; then
  profile=$(jenkee profile current 2>/dev/null | head -1)
  reason="Destructive jenkee command detected: \`${cmd}\`. ${profile:-Active profile: unknown (jenkee profile current failed)}. Confirm this is the intended Jenkins site before approving."
  jq -n --arg reason "$reason" '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"ask",permissionDecisionReason:$reason}}'
fi
