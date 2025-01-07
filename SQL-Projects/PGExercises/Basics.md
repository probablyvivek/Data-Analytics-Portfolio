-- 1. Retrieve all information from the cd.facilities table
```sql
SELECT *
FROM cd.facilities;
```

-- 2. How would you retrieve a list of only facility names and costs?
```sql
SELECT name, membercost
FROM cd.facilities;
```

-- 3. How can you produce a list of facilities that charge a fee to members?
```sql
SELECT *
FROM cd.facilities
WHERE membercost > 0;
```

-- 4. How can you produce a list of facilities that charge a fee to members, and that fee is less than 1/50th of the monthly maintenance cost? Return the facid, facility name, member cost, and monthly maintenance of the facilities in question.
```sql
SELECT facid, name, membercost, monthlymaintenance
FROM cd.facilities
WHERE membercost > 0
  AND membercost < monthlymaintenance * 1/50.0;
```

-- 5.
---
