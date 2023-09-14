# C1PolicyManagement

User Input:
	API key
  C1 Region
	
Fetch All Policies:
	API Used: GET /api/policies
	Retrieve all policies and their details.
 
Group and Compare Policies:
	Group policies based on the naming convention - 'dev-WinSvr', 'prd-WinSvr', 'qas-WinSvr'
	Compare the child policies within these groups to identify any missing one (dev ----> prd ----> qas)
 
Show Missing Policies:
	Display a list of missing policies and the groups where they're missing.

User Selection:
	User to select which missing policies they'd like to duplicate.

Duplicate Selected Policies:
	API Used: GET /api/policies/{policy_id} to fetch source policy details.
	API Used: POST /api/policies to create a new policy.
 	Duplicate the selected policies into the groups where they're missing.
