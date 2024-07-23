- [Top50 LeetCode Problems](#top50-leetcode-problems)
  - [Problem 1](#problem-1)
    - [Solution 1](#solution-1)
  - [Problem 2](#problem-2)
    - [Solution 2](#solution-2)
  - [Problem 3](#problem-3)
    - [Solution 3](#solution-3)

## Top50 LeetCode Problems

### [Problem 1](https://leetcode.com/problems/recyclable-and-low-fat-products/description/?envType=study-plan-v2&envId=top-sql-50) 

#### Solution 1
```sql
-- Write a solution to find the ids of products that are both low fat and recyclable.
SELECT product_id
FROM Products
WHERE low_fats = 'Y' AND recyclable = 'Y';
```
----
### [Problem 2](https://leetcode.com/problems/find-customer-referee/description/?envType=study-plan-v2&envId=top-sql-50)

#### Solution 2
```sql
--- Find the names of the customer that are not referred by the customer with id = 2.
SELECT name
FROM Customer
WHERE referee_id IS NULL or referee_id <>2
```
### [Problem 3](https://leetcode.com/problems/big-countries/?envType=study-plan-v2&envId=top-sql-50)

#### Solution 3
```sql
-- Write a solution to find the name, population, and area of the big countries.


```


