# AGENTS.md

## Project goal
This repository is a timetabling assistant for a tutoring centre. It is not a university timetabling engine and not a school ERP.

## Product priorities
1. Correct scheduling logic
2. Clear maintainable code
3. Fast admin workflow
4. Practical UI
5. Easy local setup

## Engineering rules
- Prefer simple, readable solutions
- Avoid overengineering
- Keep business logic separate from UI
- Keep scheduling logic well-tested
- Use explicit validation
- Keep database design clean and extensible
- Write modular code

## Scheduling rules
A session is valid only if:
- teacher is available
- student is available
- session does not overlap existing teacher bookings
- session does not overlap existing student bookings
- duration fits the slot

## Testing requirements
Always add or update tests when changing:
- overlap logic
- recurrence logic
- match ranking
- conflict detection

## Delivery style
When working on larger tasks:
1. explain the plan briefly
2. implement in small steps
3. summarise what changed
4. note any assumptions
