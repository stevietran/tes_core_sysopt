# Standard workflow

1. Create a new branch for each new feature from master branch

`git checkout -b <branchName> master`

2. Be sure to always check which branch you are before you begin working!

`git status`


3. Update your code from your local to remote repo when you finish developing the feature

``` git
git add . 
git commit -m yourMessage
git push origin <branchName>
```

4. Creat a new pull request (Optional. Not implemeted yet!)

Go to GitHub and create a new pull request. Once someone reviews the pull request, they will resolve any issues or conflicts that come up and approve the pull request to be merged into the master.

# Code branching conventions
The main repository will always hold two evergreen branches:
- master
- stable

As a developer, you will be branching and merging from master
When the source code in the master branch is stable and has been deployed, all of the changes will be merged into stable and tagged with a release number.

Supporting Branches:
- Feature branches
- Bug branches
- Hotfix branches

## Feature branches
Feature branches are used when developing a new feature or enhancement which has the potential of a development lifespan longer than a single deployment

Rules:
- Must branch from: `master`
- Must merge back into: `master`
- Branch naming convention: `feature-<feature_id>`

Working with a feature branch

```
$ git checkout -b feature-id master // create a feature branch from master
$ git push origin feature-id // makes the new feature remotely available
```
Periodically, changes made to master (if any) should be merged back into your feature branch

`$ git merge master // merges changes from master into feature branch`

## Bug branches 
Bug branches will be created when there is a bug on the live site that should be fixed and merged into the next deployment. Additionally, bug branches are used to explicitly track the difference between bug development and feature development. 

Rules:
- Must branch from: `master`
- Must merge back into: `master`
- Branch naming convention: `bug-<bug-id>`

Working with a feature branch
```
$ git checkout -b bug-id master // create a feature branch from master
$ git push origin bug-id // makes the new feature remotely available
```

Periodically, changes made to master (if any) should be merged back into your bug branch

`$ git merge master // merges changes from master into feature branch`

## Hotfix Branches
Originate from the need to act immediately upon an undesired state of a live production version

Rules:
- Must branch from: `tagged stable`
- Must merge back into: `master and stable`
- Branch naming convention: `hotfix-<hotfix-id>`

Working with hotfix branch:
```
$ git checkout -b hotfix-id stable // creates a local branch for the new hotfix
$ git push origin hotfix-id // makes the new hotfix remotely available
```



