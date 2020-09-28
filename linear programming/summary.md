### 1. the standard form
1.1 all constraints are equations  
1.2 the objective could be a maximization or minimization problem, both of them are fine.
1.3 the rank of a should be less than n (the number of variables). it means that more variables than constraints

### 2. Process
1.1 it's like we are exploring from one vertex to another vertex
1.2 so we need basic feasible solution, which is a basis
1.3 iterate the process, from one basis to another basis, during the process, improve the objective

### 3. Infeasible
1.1 change the original objective to minimize sum(slack_variables)  
1.2 add one slack varaible to one constraint, from a matrix view, it looks like A concatenate Identity matrix  
1.3 solve the problem to see if all slack variables are 0  

**It is like we didn't change much of each constraint, and the objective value is quite trival, it is obvious that we can get it**  
**IF ALL constraints constructs a feasible region**

### 4. Unbounded
1.1 Find one entering variable
1.2 No strictly positive exiting variable exist. It means we will have way more positive coefficients in the C row when doing the row operation. And the objective could be unboundedly small when it always existing postive coefficients, thus the corresponding varaibles increase, the objective decreses
