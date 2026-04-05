# Product Spec

## Product name
Timetabling Assistant for a Tutoring Centre

## Product summary
A scheduling assistant that helps an admin manage teacher availability, student constraints, recurring lessons, and rapid slot matching for new students.

## Primary user
Admin or timetable manager at a tutoring centre.

## Main problem
Manual timetable creation in Excel is slow, error-prone, and difficult to update when adding new students.

## Core use cases
1. Add and manage teachers
2. Add and manage students
3. Record teacher weekly availability
4. Record student preferences and blocked times
5. Create recurring weekly sessions
6. Suggest valid slots for a new student with a chosen teacher
7. Confirm a suggested slot and create the session

## Non-goals
- School-wide room allocation
- Exam timetabling
- University module scheduling
- Payroll
- Full CRM or ERP functionality

## Functional requirements
- Teacher CRUD
- Student CRUD
- Weekly availability input
- Student preference input
- Student blocked time input
- Session CRUD
- Clash detection
- Ranked slot suggestions
- Manual override and editing

## Quality requirements
- Fast to use
- Easy to understand
- Correct scheduling logic
- Easy to maintain
- Seeded for demo/testing
