****-- 1. Retrieve all information from the cd.facilities table
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

-- 5.How can you produce a list of all facilities with the word 'Tennis' in their name?
```sql
SELECT
	facid,
	name,
	membercost,
	guestcost,
	initialoutlay,
	monthlymaintenance
FROM cd.facilities
WHERE name LIKE '%Tennis%';
```

-- 6. How can you retrieve the details of facilities with ID 1 and 5? Try to do it without using the OR operator.
```sql
SELECT
    facid,
    name,
    membercost,
    guestcost,
    initialoutlay,
    monthlymaintenance
FROM cd.facilities
WHERE facid IN (1,5);
```

