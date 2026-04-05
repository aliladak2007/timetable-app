# Test Plan

## Core tests

### Time overlap
- overlapping ranges
- touching but non-overlapping ranges
- fully contained range
- exact match range

### Teacher availability
- slot fully inside availability
- slot partially outside availability
- slot across multiple availability windows
- no availability on that weekday

### Student preference filtering
- slot inside preferred range
- slot outside preferred range
- multiple preference windows with priorities

### Student blocked times
- direct overlap with blocked time
- adjacent but valid
- blocked time fully contains candidate slot

### Existing sessions
- teacher clash
- student clash
- both clash
- cancelled session ignored if business rule allows

### Recurrence
- weekly recurring sessions cause clash on matching weekday
- different weekday does not clash
- end-dated session is ignored after end date

### Ranking
- exact fit ranks above looser fit
- earlier slot ranks above later slot when all else equal
- compact schedule preference behaves consistently

## API tests
- create teacher
- create student
- create session
- request match suggestions
- reject invalid booking
- confirm valid booking

## Demo data tests
- seeded data loads correctly
- seeded match example returns at least one suggestion
- seeded conflict example returns no invalid suggestions
