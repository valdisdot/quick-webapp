## Quick WebApp QA

### Users and their roles

- How to add a new user role in runtime?

Since the purpose of user role is to restrict the group of user to access to a specific part of UI, there is no way to add a new user role in the runtime.
Logically, if you add/remove a role, you add/remove a role responsibility in your code and restart the application.

Thereby, you can add a role while app is not running - by adding to the predefined roles list in the UserDataSource or by inserting it into the physical data source (in role table in your user.db for example)

- How to delete a user?

The architecture of the library intensionally does not assume the user deletion (user might have done something usefull in your application so the user record must be present). 

Either set the user not active of delete the record manually when application is not running (from user table in your user.db for example)

- Is it really safe to store user cretentials in sqlite database file or a directory?

Nothing is safe by default. The administrators can setup the application process's user rights to be the only user that has access to the files, or the developers may implement their own UserDataSource and pass into into the UserService.

- Is subroles or child/parent roles supported so I specify a role on the page and all child roles will have access to?

No, current implementation treat roles as single flags only, so you must define what role has access to what.
Do a membership matrix and then implement it in the code.

- Some part of the code (like UserService.is_logged_in) uses UserSession.user to check if the user is active/is locked that may not reflect the actual state in data storage, might it allow locked/not active user enter the system?

Durring password set or user edit, the UserService removes all UserSessions (UserService.close_user_sessions) so no. 
Yes, while editing user directly in data storage but it discoureged.
