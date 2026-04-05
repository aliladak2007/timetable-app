# Schema Brief

## Suggested entities

### Teacher
- id
- full_name
- email
- subject_tags
- active

### Student
- id
- full_name
- parent_name
- contact_email
- active

### AvailabilitySlot
Represents teacher weekly availability.
- id
- teacher_id
- weekday
- start_time
- end_time

### StudentPreference
Represents preferred windows for a student.
- id
- student_id
- weekday
- start_time
- end_time
- priority

### StudentBlockedTime
Represents existing commitments or impossible times.
- id
- student_id
- weekday
- start_time
- end_time
- reason

### Session
Represents an actual recurring weekly booking.
- id
- teacher_id
- student_id
- weekday
- start_time
- end_time
- duration_minutes
- subject
- status
- start_date
- end_date nullable

### ScheduleChangeLog optional
- id
- entity_type
- entity_id
- action
- changed_by
- changed_at
- notes

## Time modelling
For MVP:
- Use weekly recurring local-time schedules
- Represent weekday as integer 0 to 6 or enum Monday to Sunday
- Store times as local time values
- Assume one business timezone for the centre
- Add a clear note in documentation about future timezone expansion

## Slot validity rules
A candidate slot is valid only if:
1. The slot fits fully within teacher availability
2. The slot fits fully within student preference or allowed time
3. The slot does not overlap an existing teacher session
4. The slot does not overlap an existing student session
5. The slot does not overlap a student blocked time
6. The slot duration matches the requested lesson duration

## Ranking approach
Base score from:
- exact preference fit
- earlier slot bonus
- compact timetable bonus
- repeatable weekly consistency
- optional teacher utilisation preference

Keep ranking explainable.
