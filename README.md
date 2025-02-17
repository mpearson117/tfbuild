# TFBuild

[Terraform](https://www.terraform.io/) build management wrapper.

## Overview

TFBuild is designed to standardize:

- **AWS Deployments**: Utilizes distributed per-account, per-environment S3-backed Terraform states.
- **Azure Deployments**: Centralized Storage Account-backed states.
- **VMware Deployments**: Uses Terraform Cloud to dynamically create execution workspaces during initialization.
- **GCP Support**: Coming soon...

## Supported Operating Systems

TFBuild currently supports:

- **MacOS** (64-bit/ARM)
- **Linux** (64-bit/ARM)
- **Windows**

## Installation

### Prerequisites

- Python **>= 3.8** (MacOS M1 requires Python **>= 3.10**).

### Installation Methods

#### 1. Install via pip:

```sh
pip install tfbuild
```

#### 2. Install from a custom PyPi repository:

```sh
pip install --extra-index-url https://<repo_url>/pypi-repo/simple tfbuild
```

#### 3. Install from source:

```sh
git clone <repo_url>.git
cd <local_repo_folder>
pip install -e .
```

## Terraform Execution Prerequisites

TFBuild assumes deployments are executed from a Git repository with the following structure:

### Git Repository Naming Conventions

#### Repository Naming Standard

- **Simple**: `<Cloud_ID>-<Project_Acronym>` (for repositories with built-in grouping, e.g., GitLab, BitBucket).
- **Extended**: `<Repository_Prefix>-<Cloud_ID>-<Project_Acronym>` (for platforms without grouping, e.g., GitHub).

#### Branch Naming Standard

- **Default**: `<Account_ID>-<Environment>`
- **Simple**: `<Environment>` (used when `Cloud_ID` does not match AWS, Azure, GCP, or VMware).

#### Example

- **Repository**: 
  - Simple: `aws-k8s`
  - Extended: `iac-aws-k8s`
- **Branch**: `234625632123-dev` or `AWSShared-dev` (without dashes in `<Account_ID>`).

### Environment-Specific Branch Layout

Terraform configurations (`*.tf`) remain consistent across branches. Changes should be merged from lower to higher environments. Terraform variables should be introduced separately per environment at the lowest environmental banch, and managed through PRs moving the changes to the required branch.

![Repo-Architecture](https://github.com/mpearson117/tfbuild/blob/main/images/repo_architecture.svg?raw=True)

## Terraform Backend Configurations

By default, the backend is selected based on the `Cloud_ID` from the repository naming convention. This can be overridden using the `backend` configuration variable in Git deployment scripts.

### Backend Options

| Backend | Description |
|---------|------------|
| `aws` | Uses AWS S3 for state management |
| `azr` | Uses Azure Storage Account |
| `tfc` | Uses Terraform Cloud |

If `Cloud_ID` is not recognized and no supported backend is configured, the deployment defaults to **local state management**.

### Global Resources

Are automatically detected if they contain `53` or `global` in their names.  
In this case `<Region>` is removed from the backend paths or TFC extended workspace names.

For declaring all resources in the project global, as in Active-Passive deployments,  
`global_resource = "true"` needs to exist in the `../common/environments/env_<Environment>.hcl` global declarations file

### 1. AWS S3 Backend

S3 buckets are an execution prerequisite, to the AWS deployment.

**Bucket Naming Standard:**  
- **Primary**: `<Bucket_Prefix>.<Account_ID>.<Environment>`  
- **Disaster Recovery (DR)**: `<Bucket_Prefix>.<Account_ID>.<Environment>.dr`  

**Example:**  
- Primary: `inf.tfstate.234625632123.dev`  
- DR: `inf.tfstate.234625632123.dev.dr`  

( `dr = "true"` needs to exist in the `../common/environments/env_<Environment>.hcl` global declarations file )
 
Buckets are bi-directionally replicated.  
Primary and a DR bucket are available, per account per environment.  
When using account targeted S3 buckets for account and environment, there should be no conflicts between states, but uniformity for ease of usage.  
 
**Backend Path:**  
- General resources: `<Project_Acronym>/<Region>/<Current_Dir>/terraform.tfvars`
- Global resources: `<Project_Acronym>/<Current_Dir>/terraform.tfvars`

### 2. Terraform Cloud Workspaces

**Workspace Naming Standard:**  
- **Simple**: `<Environment>-<Project_Acronym>-<Current_Dir>`  
- **Extended (Default)**: `<Cloud_ID>-<Environment>-<Project_Acronym>-<Region>-<Current_Dir>`
- **Extended (Global)**: `<Cloud_ID>-<Environment>-<Project_Acronym>-<Current_Dir>`

### 3. Azure Storage Account Backend

Storage Accounts must be created during subscription creation.
Similar naming as S3 buckets, but without dots, as SA names need to be alpha-numeric.
TFBuild will validate the Storage Account name length and if it is longer than the Azure supported 24 characters it will exit with a handled error.

**Storage Account Naming Standard:**  
- **Primary**: `<Bucket_Prefix><Subscription_ID><Environment>`  
- **DR**: `<Bucket_Prefix><Subscription_ID><Environment>dr`  

**Example:**  
- Primary: `inftfstateshareddev`  
- DR: `inftfstateshareddevdr`  

**Backend Path:**  
- General resources: `<Environment>/<Project_Acronym>/<Region>/<Current_Dir>/terraform.tfvars`
- Global resources: `<Environment>/<Project_Acronym>/<Current_Dir>/terraform.tfvars`

## Usage

TFBuild commands can be executed as:

```sh
tfbuild <command>
tfbuild <command>-<site>

tfb <command>
tfb <command>-<site>
```

### Supported Commands

| Command | Description |
|---------|-------------|
| `apply` | Apply Terraform configuration |
| `config` | Configure global variables |
| `destroy` | Destroy Terraform configuration |
| `destroyforce` | Destroy without confirmation |
| `help` | Display help menu |
| `init` | Initialize backend & clean local cache |
| `plan` | Create Terraform plan |
| `plandestroy` | Plan Terraform destroy scenario |
| `reinit` | Initialize backend & keep cache |
| `replan` | Re-run Terraform plan |
| `taint` | Taint specific resources |
| `test` | Test run displaying project variables |
| `tfimport` | Import existing resources |
| `update` | Update Terraform modules |
| `version` | Display TFBuild version |

Deployment Regions allow the deployment of the same code to multiple regions.  

### Example Usage

- Deploy in the designated DR site: `tfbuild apply-dr`

```sh
tfbuild init
tfbuild update
tfbuild plan
tfbuild plan-dr
tfbuild plan-us-west-2
tfbuild replan
tfbuild plandestroy
tfbuild apply
tfbuild apply-dr
tfbuild apply-us-west-2
tfbuild destroy
tfbuild taint
tfbuild test
tfbuild tfimport
tfbuild config --bucket_prefix=test_bucket --tf_cloud_org=test_org
```

Terraform options can be passed directly:

```sh
tfbuild plan -json
tfbuild apply -compact-warnings -no-color
```

## Deployment Global Variables

### Configuration File Variables

| Environment Variable | Config Variable | Description | Default | Required |
|----------------------|----------------|-------------|---------|----------|
| BUCKET_PREFIX | bucket_prefix | Override bucket prefix | `inf.tfstate` | No |
| TF_CLOUD_ORG | tf_cloud_org | Terraform Cloud organization | - | Yes |
| TF_TOKEN | - | Terraform Cloud authentication token | - | Yes |

Terraform Cloud credentials are sourced from the [Terraform CLI Config File](https://www.terraform.io/cli/config/config-file#credentials).

Introducing the ability to set global wrapper variables that preceede Git global variables for any deployment.

Here are the default search paths for each platform:
- MacOS: `~/.config/tfbuild` and `~/Library/Application Support/tfbuild`
- Other Unix: `$XDG_CONFIG_HOME/tfbuild` and `~/.config/tfbuild`
- Windows: `%APPDATA%\tfbuild` where the `APPDATA` environment variable falls back to `%HOME%\AppData\Roaming` if undefined

### Variables from Git Repository

| Variable | Description | Required |
|----------|-------------|----------|
| account | Deployment `Account_ID` from branch name | Yes |
| cloud | Deployment `Cloud_ID` from repo name | Yes |
| env | Deployment `Environment` from branch name | Yes |
| project | Deployment `Project_Acronym` from repo name | Yes |

### Variables sourced from Git Deployment scripts repository common shell files

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
| backend | Backend type override | Cloud Backend | `` | no |
| backend_region | Hardcoded tf remote state backend S3/SA region | Cloud Backend | `us-east-1` | yes |
| china_deployment | Hardcoded tf remote state backend switch. Can be activated with `china_deployment = "true"` | AWS Backend | `cn-north-1` | yes |
| dr | Backend S3/SA `backend_region` switch from primary to secondary `us-west-2`. Can be activated with `dr = "true"` | Cloud Backend | - | no |
| global_resource | Declaring all resources in the project global, `global_resource = "true"` | AWS Backend | - | no |
| mode | For in-region `blue/green` deployment by setting the variable accordingly | All Backends | - | no |
| region | Deployment region, used in remote state backend path | Cloud Backend Key | - | yes |
| *site | In region secondary site deployment designation | All Backends | - | no |
| tf_cli_args | Custom TF variables to be passed to the deployment | TER | - | no |
| tf_cloud_backend | TFC Backend. Can be activated with `tf_cloud_backend = "true"` **will be deprecated in favor of `backend = tfc`** | TFC Backend (VMW) | - | yes |
| tf_cloud_org | Terraform Cloud Organization | TFC Backend (VMW) | - | no |
| target_environment_type | Switch between multi-region and in region multi-site deployment types. Defaults to multi-region. | All Backends | `region` | no |


### Variables exposed to the Terraform deployment scripts:

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

## Upgrade

```sh
pip install --upgrade tfbuild
```

## Uninstall

```sh
pip uninstall tfbuild
```
