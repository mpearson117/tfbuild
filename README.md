
**TFBuild**
=======
<br /> 

[Terraform](https://www.terraform.io/) build management wrapper.
This wrapper is primarily built to standardise:
- AWS deployments with distributed per account, per environment S3 backed terraform states 
- Azure deployments with central Storage Account backed states
- VMware deployments with TF Cloud to store states in per execution TF Cloud Workspaces, which it will create dynamically during the init process.
- GCP implementation also possible, coming soon...

## Support
<br /> 

Currently tfbuild supports the following Operating Systems:
- MacOS (64bit/Arm)
- Linux (64bit/Arm)
- Windows

## Installation
<br /> 

1. Python > 3.8 required (3.10 and higher on MacOS M1)

2. Install with pip (coming soon):

```sh
pip install tfbuild
```

3. Install TFBuild from wheel package published to custom pypi repo URL:

  ```sh
  $ pip install --extra-index-url https://<repo_url>/pypi-repo/simple tfbuild
  ```

4. Install TFBuild from source repo:

```sh
clone <repo_url>.git
cd <local_repo_folder>
pip install -e .
```

## Terraform execution prerequisites
<br /> 

tfbuild assumes that the deployment is executed from a git repository with the following setup:

### GIT Repository - Naming Conventions and Architecture
<br /> 

Repository Naming Standard: `<Cloud_ID>-<Project_Acronym>`
Branch Naming Standard: `<Account_ID>-<Environment>`
 
Example:
-	Repository: `aws-k8s`
-	Branch: `234625632123-dev` os something like `AWSShared-dev`, with no dashes in `<Account_ID>`
 
### GIT Repository - Environment Specific branch layout
<br /> 

Terraform Configurations `*.tf` are templatized, and should not change between branches.  
Managed SDLC practices are advised to merge changes from lower environments and up.  
Terraform variables should be introduced separately for each environment and site at the lowest environmental banch, and PRs used for moving the changes to the required branch.  

![Repo-Architecture](./images/repo_architecture.svg) 

### Terraform State - AWS S3 Bucket Name
<br /> 

S3 buckets are an execution prerequisite, usually built as part of an AWS deployment.
TFState, S3 bucket naming standard:
- Primary Bucket Naming Standard: `<Bucket_Prefix>.<Account_ID>.<Environment>`
- DR Bucket Naming Standards: `<Bucket_Prefix>.<Account_ID>.<Environment>.dr`

Example:
- Primary Bucket Name: `inf.tfstate.234625632123.dev`
- DR Bucket Name: `inf.tfstate.234625632123.dev.dr`

( `dr = "true"` needs to exist in the `../common/environments/env_<Environment>.hcl` global declarations file )
 
Buckets are bi-directionally replicated.  
Primary and a DR bucket are available, per account per environment.  
When using account targeted S3 buckets for account and environment, there should be no conflicts between states, but uniformity for ease of usage.  
 
Backend Path:
- General resources backend path: `<Project_acronym>/<Region>/<Current_Dir>/terraform.tfvars`
- Backend resources backend path: `<Project_acronym>/<Current_Dir>/terraform.tfvars`

Curently the only global resource that is automatically detected is `Route-53`.

For declaring all resources in the project global, as in Active-Passive deployments,  
`global_resource = "true"` needs to exist in the `../common/environments/env_<Environment>.hcl` global declarations file

### Terraform State - TF Cloud Workspaces
<br /> 

- Workspace Naming standard: `<Environment>-<Project_Acronym>-<Current_Dir>`

As workspaces are curently only used for VMware deployment, a `<Cloud_ID>` is not used but will be introduced:
- Future Workspace Naming Standard: `<Cloud_ID>-<Environment>-<Project_Acronym>-<Current_Dir>`

### Terraform State - Azure Storage Accounts
<br /> 

Storage Accounts are an execution prerequisite, should be created during a Subscription creation.  
Similar naming as S3 buckets, but without dots, as SA names need to be alpha-numeric:

Storage Account Naming Standard: 
- Primary SA Naming Standard: `<Bucket_Prefix><Subscription_ID><Environment>`
- DR SA Naming Standards: `<Bucket_Prefix><Subscription_ID><Environment>.dr`

Example:
- Primary SA Name: `inftfstateshareddev`
- DR SA Name: `inftfstateshareddevdr`

## Usage
<br /> 

App name is `tfbuild` or `tfb`

```sh
tfbuild <command>
tfbuild <command>-<site>

tfb <command>
tfb <command>-<site>
```

Commands, execute specific Terraform task:
| Command | Description |
|---------|-------------|
| `apply` | Apply Terraform configuration |
| `destroy` | Destroy Terraform Configuration |
| `destroyforce` | Destroy Terraform Configuration with no prompt |
| `help` | Display the help menu that shows available commands |
| `init` | Initialize Terraform backend and clean local cache |
| `plan` | Create Terraform plan with clean local cache |
| `plandestroy` | Create a Plan for a Destroy scenario |
| `reinit` | Initialize Terraform backend and keep local cache |
| `replan` | Create Terraform plan with existing local cache |
| `taint` | Taint specific module and resources |
| `test` | Test run showing all project variables |
| `tfimport` | Import states for existing resources |
| `update` | Update Terraform modules |
| `version` | TFBuild version |

Deployment Regions allow the deployment of the same code to multiple regions.  
Example:  
- Deploy in the designated DR site: `tfbuild apply-dr`

```sh
# Usage Examples:

$ tfbuild init
$ tfbuild update
$ tfbuild plan
$ tfbuild plan-dr
$ tfbuild plan-us-west-2
$ tfbuild replan
$ tfbuild plandestroy
$ tfbuild apply
$ tfbuild apply-dr
$ tfbuild apply-us-west-2
$ tfbuild destroy
$ tfbuild taint
$ tfbuild test
$ tfbuild tfimport
```

## Deployment Global Variable Reference
<br /> 

### Install Configuration file
<br /> 

| Variable | Description | Usage Target | Default | Required |
|----------|-------------|:------------:|:-------:|:--------:|
| bucket_prefix | Ability to override `Bucket_Prefix` | Cloud Backend | `inf.tfstate` | no |
| tf_cloud_org | Ability to set a global TFC org. Takes priority over Git variables. | TFC Backend (VMW) | - | yes |
<br />

Introducing the ability to set global wrapper variables that preceede Git global variables for any deployment.

Here are the default search paths for each platform:
- MacOS: `~/.config/tfbuild` and `~/Library/Application Support/tfbuild`
- Other Unix: `$XDG_CONFIG_HOME/tfbuild` and `~/.config/tfbuild`
- Windows: `%APPDATA%\tfbuild` where the `APPDATA` environment variable falls back to `%HOME%\AppData\Roaming` if undefined

### Variables sourced from Git Deployment scripts repository naming conventions
<br /> 

| Variable | Description | Usage Target | Default | Required |
|----------|-------------|:------------:|:-------:|:--------:|
| account | Deployment `Account_ID`, sourced from the Deployment Git repository branch name | Cloud Backend | - | yes |
| cloud | Deployment `Cloud_ID`, sourced from the Deployment Git repository name | All Backend | - | yes |
| env | Deployment `Environment`, sourced from the Deployment Git repository branch name | All Backends | - | yes |
| project | Deployment `Project_acronym`, sourced from the Deployment Git repository name | All Backend | - | yes |
<br />


### Variables sourced from Git Deployment scripts repository common shell files
<br /> 

Project environment and site specific:
- The `<REPO_PATH>/common/environments/env_<Environment>.hcl` environment file, for unisite deployments.  
- The `<REPO_PATH>/common/environments/env_<Environment>_<SITE_NAME>.hcl` environment file, for multi-site deployments.  
Environment and site specific, not changeable per resource.

Variables declared in the environment file are declared as runtime variables, usable both in Linux and Windows deployments.  
Example: `dr = "true"`

Speciffic deployment site can be configured as per the Repo architecture above, and can be called by appending a `-<site>' to any command:
Example: `tfbuild <command>-<site>`

| Variable | Description | Usage Target | Default | Required |
|----------|-------------|:------------:|:-------:|:--------:|
| backend_region | Hardcoded tf remote state backend S3/SA region | Cloud Backend | `us-east-1` | yes |
| china_deployment | Hardcoded tf remote state backend switch. Can be activated with `china_deployment = "true"` | AWS Backend | `cn-north-1` | yes |
| dr | Backend S3/SA `backend_region` switch from primary to secondary `us-west-2`. Can be activated with `dr = "true"` | Cloud Backend | - | no |
| global_resource | Declaring all resources in the project global, `global_resource = "true"` | AWS Backend | - | no |
| mode | For in-region `blue/green` deployment by setting the variable accordingly | All Backends | - | no |
| region | Deployment region, used in remote state backend path | Cloud Backend Key | - | yes |
| *site | In region secondary site deployment designation | All Backends | - | no |
| tf_cli_args | Custom TF variables to be passed to the deployment | TER | - | no |
| tf_cloud_backend | TFC Backend. Can be activated with `tf_cloud_backend = "true"` | TFC Backend (VMW) | - | yes |
| tf_cloud_org | Terraform Cloud Organization | TFC Backend (VMW) | - | yes |
<br />


### Variables exposed to the Terraform deployment scripts:
<br /> 

These variables are useful for resource naming, and in same deployment, inter-execution linking of remote state outputs

Terraform env speciffic wrapper variables injected into Terraform.  
Variable declarations are needed in coresponding deployment `variables.tf` file"


| Variable | Description | Required |
|----------|-------------|:--------:|
| account | Exposed to Terraform, alternate to TF self identification routine | no |
| azrsa | Azure Storage Account name `bucket` equivalent) | no |
| backend_region | Used in `terraform_remote_state`, as bucket region | no |
| bucket | Used in `terraform_remote_state`, as bucket name | no |
| china_deployment | Logic selector (`ARN` for example) | no |
| deployment_region | Used in `terraform_remote_state` key | yes |
| env | Deployment environment, used in naming project speciffic resources | yes |
| mode | Exposed to Terraform, used in naming blue/green speciffic resources | no |
| prefix | A dynamic combination of `project`, `mode` and `site` | no |
| project | Project acronym, used in naming project speciffic resources | yes |
| site | Used in naming site speciffic resources | no |
| tf_cli_args | Custom TF variables to be passed to the deployment | no |
<br />


## Upgrade
<br /> 

```sh
$ pip install --upgrade tfbuild
```

## Uninstall
<br /> 

```sh
$ pip uninstall tfbuild
```
